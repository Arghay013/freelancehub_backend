from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound
from django.utils import timezone
from django.db import transaction

from .models import Order
from .serializers import OrderSerializer, OrderCreateSerializer, OrderStatusUpdateSerializer
from apps.marketplace.models import Service
from apps.accounts.permissions import IsBuyer, IsSeller
from apps.notifications.utils import notify


def safe_notify(user, event, message):
    """
    ✅ notify() কখনও crash করলে যেন order create/update 500 না দেয়
    """
    try:
        notify(user, event, message)
    except Exception as e:
        # চাইলে এখানে logging করে রাখতে পারো
        # import logging
        # logging.getLogger(__name__).exception("notify failed: %s", e)
        pass


class OrderCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsBuyer]
    serializer_class = OrderCreateSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        # ✅ Email verify check
        # profile না থাকলে AttributeError এ 500 হতে পারে, তাই safe check
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

        order = Order.objects.create(
            buyer=request.user,
            seller=service.seller,
            service=service,
            buyer_requirements=ser.validated_data.get("buyer_requirements", ""),
        )

        # ✅ notifications must not crash API
        safe_notify(order.seller, "ORDER_PLACED", f"New order placed for: {service.title}")
        safe_notify(order.buyer, "ORDER_PLACED", f"Order placed successfully for: {service.title}")

        # ✅ serializer context pass (some serializers need request)
        return Response(
            OrderSerializer(order, context={"request": request}).data,
            status=201
        )


class BuyerOrderListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsBuyer]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return (
            Order.objects
            .filter(buyer=self.request.user)
            .select_related("service", "buyer", "seller")
            .order_by("-created_at")
        )


class SellerOrderListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsSeller]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return (
            Order.objects
            .filter(seller=self.request.user)
            .select_related("service", "buyer", "seller")
            .order_by("-created_at")
        )


class SellerOrderStatusUpdateView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsSeller]
    serializer_class = OrderStatusUpdateSerializer
    queryset = Order.objects.select_related("buyer", "seller", "service").all()

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        order = self.get_object()
        if order.seller != request.user:
            raise PermissionDenied("Not your order")

        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)

        new_status = ser.validated_data["status"]
        order.status = new_status

        if new_status == Order.STATUS_COMPLETED:
            order.completed_at = timezone.now()

        order.save()

        safe_notify(order.buyer, "ORDER_UPDATED", f"Order #{order.id} status updated to {new_status}")
        safe_notify(order.seller, "ORDER_UPDATED", f"Order #{order.id} status updated to {new_status}")

        return Response(
            OrderSerializer(order, context={"request": request}).data
        )