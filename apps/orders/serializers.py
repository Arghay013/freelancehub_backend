from rest_framework import serializers
from .models import Order
from apps.marketplace.serializers import ServiceSerializer
from django.contrib.auth.models import User

class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id","username"]

class OrderSerializer(serializers.ModelSerializer):
    service = ServiceSerializer(read_only=True)
    buyer = UserMiniSerializer(read_only=True)
    seller = UserMiniSerializer(read_only=True)
    class Meta:
        model = Order
        fields = ["id","service","buyer","seller","status","buyer_requirements","created_at","updated_at","completed_at"]

class OrderCreateSerializer(serializers.Serializer):
    service_id = serializers.IntegerField()
    buyer_requirements = serializers.CharField(allow_blank=True, required=False)

class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES)
