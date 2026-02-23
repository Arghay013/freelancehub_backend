from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError, NotFound
from django.utils import timezone

from .models import Order
from .serializers import OrderSerializer, OrderCreateSerializer, OrderStatusUpdateSerializer
from apps.marketplace.models import Service
from apps.accounts.permissions import IsBuyer, IsSeller
from apps.notifications.utils import notify

class OrderCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsBuyer]
    serializer_class = OrderCreateSerializer

    def create(self, request, *args, **kwargs):
        if not request.user.profile.is_email_verified:
            raise PermissionDenied("Email not verified")

        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)

        try:
            service = Service.objects.select_related("seller").get(id=ser.validated_data["service_id"])
        except Service.DoesNotExist:
            raise NotFound("Service not found")

        order = Order.objects.create(
            buyer=request.user,
            seller=service.seller,
            service=service,
            buyer_requirements=ser.validated_data.get("buyer_requirements","")
        )
        notify(order.seller, "ORDER_PLACED", f"New order placed for: {service.title}")
        notify(order.buyer, "ORDER_PLACED", f"Order placed successfully for: {service.title}")
        return Response(OrderSerializer(order).data, status=201)

class BuyerOrderListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsBuyer]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(buyer=self.request.user).select_related("service","buyer","seller").order_by("-created_at")

class SellerOrderListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsSeller]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(seller=self.request.user).select_related("service","buyer","seller").order_by("-created_at")

class SellerOrderStatusUpdateView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsSeller]
    serializer_class = OrderStatusUpdateSerializer
    queryset = Order.objects.all()

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

        notify(order.buyer, "ORDER_UPDATED", f"Order #{order.id} status updated to {new_status}")
        notify(order.seller, "ORDER_UPDATED", f"Order #{order.id} status updated to {new_status}")
        return Response(OrderSerializer(order).data)
