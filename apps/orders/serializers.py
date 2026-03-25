from rest_framework import serializers
from django.contrib.auth.models import User

from .models import Order
from apps.marketplace.serializers import ServiceSerializer


class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]


class OrderSerializer(serializers.ModelSerializer):
    service = ServiceSerializer(read_only=True)
    buyer = UserMiniSerializer(read_only=True)
    seller = UserMiniSerializer(read_only=True)
    payment_status = serializers.SerializerMethodField()
    payment_tran_id = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "service",
            "buyer",
            "seller",
            "status",
            "buyer_requirements",
            "seller_update_message",
            "buyer_response_note",
            "seller_updated_at",
            "buyer_reviewed_at",
            "payment_status",
            "payment_tran_id",
            "created_at",
            "updated_at",
            "completed_at",
        ]

    def get_payment_status(self, obj):
        payment = getattr(obj, "payment", None)
        return getattr(payment, "status", None)

    def get_payment_tran_id(self, obj):
        payment = getattr(obj, "payment", None)
        return getattr(payment, "tran_id", None)


class OrderCreateSerializer(serializers.Serializer):
    service_id = serializers.IntegerField()
    buyer_requirements = serializers.CharField(allow_blank=True, required=False)


class SellerUpdateSerializer(serializers.Serializer):
    seller_update_message = serializers.CharField()


class BuyerReviewSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["accept", "reject"])
    buyer_response_note = serializers.CharField(allow_blank=True, required=False)


class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[Order.STATUS_IN_PROGRESS, Order.STATUS_COMPLETED])