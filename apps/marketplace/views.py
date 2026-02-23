from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied, ValidationError
from django_filters.rest_framework import DjangoFilterBackend

from .models import Service, Review
from .serializers import ServiceSerializer, ServiceCreateSerializer, ReviewSerializer
from apps.accounts.permissions import IsSeller, IsBuyer
from apps.orders.models import Order

class ServiceListCreateView(generics.ListCreateAPIView):
    queryset = Service.objects.select_related("seller").all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["category"]
    ordering_fields = ["price","created_at"]
    search_fields = ["title","description"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ServiceCreateSerializer
        return ServiceSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), IsSeller()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        if not self.request.user.profile.is_email_verified:
            raise PermissionDenied("Email not verified")
        serializer.save(seller=self.request.user)

class ServiceRetrieveView(generics.RetrieveAPIView):
    queryset = Service.objects.select_related("seller").all()
    serializer_class = ServiceSerializer
    permission_classes = [permissions.AllowAny]

class ReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        service_id = self.kwargs["service_id"]
        return Review.objects.filter(order__service_id=service_id).select_related("buyer").order_by("-created_at")

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), IsBuyer()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        if not self.request.user.profile.is_email_verified:
            raise PermissionDenied("Email not verified")

        order_id = self.request.data.get("order_id")
        rating = int(self.request.data.get("rating", 0))
        comment = self.request.data.get("comment", "")

        if rating < 1 or rating > 5:
            raise ValidationError({"rating": "Rating must be 1..5"})

        try:
            order = Order.objects.select_related("service","seller","buyer").get(id=order_id)
        except Order.DoesNotExist:
            raise ValidationError({"order_id": "Invalid order"})

        if order.buyer != self.request.user:
            raise PermissionDenied("Not your order")
        if order.status != Order.STATUS_COMPLETED:
            raise ValidationError({"detail": "You can review only after completion"})

        serializer.save(order=order, buyer=self.request.user, seller=order.seller, rating=rating, comment=comment)
