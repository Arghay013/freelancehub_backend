from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError
from django.utils import timezone
from django.db import transaction

from .models import Order
from .serializers import (
    OrderSerializer,
    OrderCreateSerializer,
    SellerUpdateSerializer,
    BuyerReviewSerializer,
    OrderStatusUpdateSerializer,
)
from apps.marketplace.models import Service
from apps.accounts.permissions import IsBuyer, IsSeller
from apps.notifications.utils import notify


def safe_notify(user, event, message):
    try:
        notify(user, event, message)
    except Exception:
        pass


class OrderCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsBuyer]
    serializer_class = OrderCreateSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        profile = getattr(request.user, "profile", None)
        if not profile or not profile.is_email_verified:
            raise PermissionDenied("Email not verified")

        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)

        service_id = ser.validated_data["service_id"]

        try:
            service = Service.objects.select_related("seller").get(id=service_id)
        except Service.DoesNotExist:
            raise NotFound("Service not found")

        if service.seller == request.user:
            raise ValidationError({"detail": "You cannot request your own service"})

        order = Order.objects.create(
            buyer=request.user,
            seller=service.seller,
            service=service,
            status=Order.STATUS_REQUESTED,
            buyer_requirements=ser.validated_data.get("buyer_requirements", ""),
        )

        safe_notify(
            order.seller,
            "ORDER_REQUESTED",
            f"New request received for '{service.title}'. Please review and send your update.",
        )
        safe_notify(
            order.buyer,
            "ORDER_REQUESTED",
            f"Your request for '{service.title}' has been sent to the seller.",
        )

        return Response(OrderSerializer(order, context={"request": request}).data, status=201)


class BuyerOrderListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsBuyer]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return (
            Order.objects.filter(buyer=self.request.user)
            .select_related("service", "buyer", "seller", "payment")
            .order_by("-created_at")
        )


class SellerOrderListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsSeller]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return (
            Order.objects.filter(seller=self.request.user)
            .select_related("service", "buyer", "seller", "payment")
            .order_by("-created_at")
        )


class SellerOrderUpdateView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsSeller]
    serializer_class = SellerUpdateSerializer
    queryset = Order.objects.select_related("buyer", "seller", "service", "payment").all()

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        order = self.get_object()
        if order.seller != request.user:
            raise PermissionDenied("Not your order")

        if order.status not in [Order.STATUS_REQUESTED, Order.STATUS_CHANGES_REQUESTED]:
            raise ValidationError({"detail": "Seller update is allowed only for requested or rejected orders"})

        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)

        order.seller_update_message = ser.validated_data["seller_update_message"].strip()
        order.status = Order.STATUS_SELLER_UPDATED
        order.seller_updated_at = timezone.now()
        order.save(update_fields=["seller_update_message", "status", "seller_updated_at", "updated_at"])

        safe_notify(
            order.buyer,
            "SELLER_UPDATED",
            f"Seller sent an update for order #{order.id}. Please accept or reject it.",
        )
        safe_notify(
            order.seller,
            "SELLER_UPDATED",
            f"Your update for order #{order.id} was sent to the buyer.",
        )

        return Response(OrderSerializer(order, context={"request": request}).data)


class BuyerOrderReviewView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsBuyer]
    serializer_class = BuyerReviewSerializer
    queryset = Order.objects.select_related("buyer", "seller", "service", "payment").all()

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        order = self.get_object()
        if order.buyer != request.user:
            raise PermissionDenied("Not your order")

        if order.status != Order.STATUS_SELLER_UPDATED:
            raise ValidationError({"detail": "Buyer can review only after seller submits an update"})

        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)

        action = ser.validated_data["action"]
        note = ser.validated_data.get("buyer_response_note", "").strip()

        order.buyer_response_note = note
        order.buyer_reviewed_at = timezone.now()

        if action == "accept":
            order.status = Order.STATUS_AWAITING_PAYMENT
            order.save(update_fields=["buyer_response_note", "buyer_reviewed_at", "status", "updated_at"])
            safe_notify(
                order.buyer,
                "ORDER_ACCEPTED",
                f"You accepted seller update for order #{order.id}. এখন payment করতে পারবেন.",
            )
            safe_notify(
                order.seller,
                "ORDER_ACCEPTED",
                f"Buyer accepted your update for order #{order.id}. Waiting for payment.",
            )
        else:
            order.status = Order.STATUS_CHANGES_REQUESTED
            order.save(update_fields=["buyer_response_note", "buyer_reviewed_at", "status", "updated_at"])
            safe_notify(
                order.buyer,
                "ORDER_REJECTED",
                f"You rejected seller update for order #{order.id}. Seller will work again.",
            )
            safe_notify(
                order.seller,
                "ORDER_REJECTED",
                f"Buyer requested changes for order #{order.id}. Please update again.",
            )

        return Response(OrderSerializer(order, context={"request": request}).data)


class SellerOrderStatusUpdateView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsSeller]
    serializer_class = OrderStatusUpdateSerializer
    queryset = Order.objects.select_related("buyer", "seller", "service", "payment").all()

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        order = self.get_object()
        if order.seller != request.user:
            raise PermissionDenied("Not your order")

        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        new_status = ser.validated_data["status"]

        if new_status == Order.STATUS_IN_PROGRESS:
            if order.status != Order.STATUS_AWAITING_PAYMENT:
                raise ValidationError({"detail": "Order can move to IN_PROGRESS only after buyer accepts and pays"})

        if new_status == Order.STATUS_COMPLETED:
            if order.status != Order.STATUS_IN_PROGRESS:
                raise ValidationError({"detail": "Order can be completed only from IN_PROGRESS state"})
            order.completed_at = timezone.now()

        order.status = new_status
        save_fields = ["status", "updated_at"]
        if new_status == Order.STATUS_COMPLETED:
            save_fields.append("completed_at")
        order.save(update_fields=save_fields)

        safe_notify(order.buyer, "ORDER_UPDATED", f"Order #{order.id} status updated to {new_status}")
        safe_notify(order.seller, "ORDER_UPDATED", f"Order #{order.id} status updated to {new_status}")

        return Response(OrderSerializer(order, context={"request": request}).data)