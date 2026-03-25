import os
import json
import uuid
from decimal import Decimal
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied, ValidationError, NotFound

from apps.accounts.permissions import IsBuyer
from apps.orders.models import Order
from apps.notifications.utils import notify
from .models import PaymentTransaction


def safe_notify(user, event, message):
    try:
        notify(user, event, message)
    except Exception:
        pass


def _post_form(url: str, data: dict) -> dict:
    payload = urlencode(data).encode("utf-8")
    req = Request(url, data=payload, headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8", errors="ignore")
    try:
        return json.loads(raw)
    except Exception:
        return {"raw": raw}


def _get_json(url: str) -> dict:
    req = Request(url, headers={"Accept": "application/json"})
    with urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8", errors="ignore")
    try:
        return json.loads(raw)
    except Exception:
        return {"raw": raw}


def _ssl_base():
    sandbox = (os.getenv("SSLC_SANDBOX", "true").lower() == "true")
    if sandbox:
        return {
            "session": "https://sandbox.sslcommerz.com/gwprocess/v4/api.php",
            "validate": "https://sandbox.sslcommerz.com/validator/api/validationserverAPI.php",
        }
    return {
        "session": "https://securepay.sslcommerz.com/gwprocess/v4/api.php",
        "validate": "https://securepay.sslcommerz.com/validator/api/validationserverAPI.php",
    }


def _frontend_url():
    return os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")


def _backend_base(request):
    env_base = os.getenv("BACKEND_URL", "").rstrip("/")
    if env_base:
        return env_base
    return request.build_absolute_uri("/").rstrip("/")


@method_decorator(csrf_exempt, name="dispatch")
class SSLCommerzInitView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsBuyer]

    @transaction.atomic
    def post(self, request):
        profile = getattr(request.user, "profile", None)
        if not profile or not profile.is_email_verified:
            raise PermissionDenied("Email not verified")

        order_id = request.data.get("order_id")
        if not order_id:
            raise ValidationError({"order_id": "order_id is required"})

        try:
            order = Order.objects.select_related("service", "buyer", "seller").get(id=int(order_id))
        except Exception:
            raise NotFound("Order not found")

        if order.buyer != request.user:
            raise PermissionDenied("Not your order")

        if order.status != Order.STATUS_AWAITING_PAYMENT:
            raise ValidationError({"detail": "Payment is allowed only after buyer accepts seller update"})

        existing_payment = getattr(order, "payment", None)
        if existing_payment and existing_payment.status == PaymentTransaction.STATUS_PAID:
            raise ValidationError({"detail": "This order is already paid"})

        name = (request.data.get("name") or "").strip()
        phone = (request.data.get("phone") or "").strip()
        address = (request.data.get("address") or "").strip()

        if not name:
            raise ValidationError({"name": "Name is required"})
        if not phone:
            raise ValidationError({"phone": "Phone is required"})
        if not address:
            raise ValidationError({"address": "Address is required"})

        tran_id = existing_payment.tran_id if existing_payment else f"FH-{uuid.uuid4().hex[:24]}"
        amount = Decimal(order.service.price)

        if existing_payment:
            pay = existing_payment
            pay.amount = amount
            pay.customer_name = name
            pay.customer_phone = phone
            pay.customer_address = address
            pay.status = PaymentTransaction.STATUS_INITIATED
            pay.raw_init_response = None
            pay.raw_validation = None
            pay.save()
        else:
            pay = PaymentTransaction.objects.create(
                order=order,
                tran_id=tran_id,
                amount=amount,
                customer_name=name,
                customer_phone=phone,
                customer_address=address,
                status=PaymentTransaction.STATUS_INITIATED,
            )

        base = _ssl_base()
        store_id = os.getenv("SSLC_STORE_ID", "").strip()
        store_pass = os.getenv("SSLC_STORE_PASS", "").strip()

        if not store_id or not store_pass:
            raise ValidationError("SSLC_STORE_ID / SSLC_STORE_PASS not configured in backend env")

        backend_base = _backend_base(request)
        success_url = f"{backend_base}/api/payments/sslcommerz/success/"
        fail_url = f"{backend_base}/api/payments/sslcommerz/fail/"
        cancel_url = f"{backend_base}/api/payments/sslcommerz/cancel/"

        payload = {
            "store_id": store_id,
            "store_passwd": store_pass,
            "total_amount": str(amount),
            "currency": "BDT",
            "tran_id": tran_id,
            "success_url": success_url,
            "fail_url": fail_url,
            "cancel_url": cancel_url,
            "product_name": order.service.title,
            "product_category": order.service.category,
            "product_profile": "general",
            "cus_name": name,
            "cus_phone": phone,
            "cus_add1": address,
            "cus_city": "Dhaka",
            "cus_country": "Bangladesh",
            "cus_email": request.user.email or "buyer@example.com",
            "ship_name": name,
            "ship_add1": address,
            "ship_city": "Dhaka",
            "ship_country": "Bangladesh",
            "value_a": str(order.id),
            "value_b": str(request.user.id),
            "multi_card_name": "",
        }

        resp = _post_form(base["session"], payload)
        pay.raw_init_response = resp
        pay.save(update_fields=["raw_init_response", "updated_at"])

        gateway_url = resp.get("GatewayPageURL") or resp.get("gatewaypageurl")
        if not gateway_url:
            raise ValidationError({"detail": "Failed to create payment session", "ssl": resp})

        safe_notify(order.buyer, "PAYMENT_INITIATED", f"Payment started for order #{order.id}.")
        safe_notify(order.seller, "PAYMENT_INITIATED", f"Buyer started payment for order #{order.id}.")

        return Response({"gateway_url": gateway_url, "tran_id": tran_id, "order_id": order.id})


def _validate_payment(val_id: str):
    base = _ssl_base()
    store_id = os.getenv("SSLC_STORE_ID", "").strip()
    store_pass = os.getenv("SSLC_STORE_PASS", "").strip()

    qs = urlencode(
        {
            "val_id": val_id,
            "store_id": store_id,
            "store_passwd": store_pass,
            "v": "1",
            "format": "json",
        }
    )
    url = f"{base['validate']}?{qs}"
    return _get_json(url)


def _redirect_front(status: str, tran_id: str, order_id: int):
    front = _frontend_url()
    return HttpResponseRedirect(f"{front}/payment/{status}?tran_id={tran_id}&order_id={order_id}")


@csrf_exempt
def ssl_success(request):
    val_id = request.POST.get("val_id") or request.GET.get("val_id")
    tran_id = request.POST.get("tran_id") or request.GET.get("tran_id")

    if not tran_id:
        return _redirect_front("fail", "unknown", 0)

    try:
        pay = PaymentTransaction.objects.select_related("order", "order__buyer", "order__seller").get(tran_id=tran_id)
    except PaymentTransaction.DoesNotExist:
        return _redirect_front("fail", tran_id, 0)

    if not val_id:
        pay.status = PaymentTransaction.STATUS_FAILED
        pay.save(update_fields=["status", "updated_at"])
        return _redirect_front("fail", tran_id, pay.order.id)

    validation = _validate_payment(val_id)
    pay.raw_validation = validation

    status = (validation.get("status") or "").lower()
    if status in ["valid", "validated"]:
        pay.status = PaymentTransaction.STATUS_PAID
        pay.save(update_fields=["status", "raw_validation", "updated_at"])

        order = pay.order
        order.status = Order.STATUS_IN_PROGRESS
        order.save(update_fields=["status", "updated_at"])

        safe_notify(order.buyer, "PAYMENT_SUCCESS", f"Payment successful for order #{order.id}.")
        safe_notify(order.seller, "PAYMENT_SUCCESS", f"Buyer paid successfully for order #{order.id}. You can continue delivery.")

        return _redirect_front("success", tran_id, order.id)

    pay.status = PaymentTransaction.STATUS_FAILED
    pay.save(update_fields=["status", "raw_validation", "updated_at"])
    safe_notify(pay.order.buyer, "PAYMENT_FAILED", f"Payment failed for order #{pay.order.id}.")
    return _redirect_front("fail", tran_id, pay.order.id)


@csrf_exempt
def ssl_fail(request):
    tran_id = request.POST.get("tran_id") or request.GET.get("tran_id") or "unknown"
    try:
        pay = PaymentTransaction.objects.select_related("order", "order__buyer").get(tran_id=tran_id)
        pay.status = PaymentTransaction.STATUS_FAILED
        pay.save(update_fields=["status", "updated_at"])
        safe_notify(pay.order.buyer, "PAYMENT_FAILED", f"Payment failed for order #{pay.order.id}.")
        return _redirect_front("fail", tran_id, pay.order.id)
    except PaymentTransaction.DoesNotExist:
        return _redirect_front("fail", tran_id, 0)


@csrf_exempt
def ssl_cancel(request):
    tran_id = request.POST.get("tran_id") or request.GET.get("tran_id") or "unknown"
    try:
        pay = PaymentTransaction.objects.select_related("order", "order__buyer").get(tran_id=tran_id)
        pay.status = PaymentTransaction.STATUS_CANCELLED
        pay.save(update_fields=["status", "updated_at"])
        safe_notify(pay.order.buyer, "PAYMENT_CANCELLED", f"Payment cancelled for order #{pay.order.id}.")
        return _redirect_front("cancel", tran_id, pay.order.id)
    except PaymentTransaction.DoesNotExist:
        return _redirect_front("cancel", tran_id, 0)