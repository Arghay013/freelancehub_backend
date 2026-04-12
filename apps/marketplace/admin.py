from django.contrib import admin
from .models import Service, Review


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "seller",
        "category",
        "price",
        "delivery_time_days",
        "created_at",
    )
    list_filter = ("category", "created_at")
    search_fields = ("title", "description", "seller__username")
    ordering = ("-created_at",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "buyer", "seller", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("buyer__username", "seller__username", "comment")
    ordering = ("-created_at",)