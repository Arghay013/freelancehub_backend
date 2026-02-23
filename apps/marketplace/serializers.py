from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Service, Review

class SellerMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]

class ServiceSerializer(serializers.ModelSerializer):
    seller = SellerMiniSerializer(read_only=True)
    class Meta:
        model = Service
        fields = ["id","seller","title","description","requirements","price","category","delivery_time_days","created_at"]

class ServiceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ["title","description","requirements","price","category","delivery_time_days"]

class ReviewSerializer(serializers.ModelSerializer):
    buyer = SellerMiniSerializer(read_only=True)
    class Meta:
        model = Review
        fields = ["id","rating","comment","buyer","created_at"]
