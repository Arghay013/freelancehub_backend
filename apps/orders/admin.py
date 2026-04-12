from django.contrib import admin
from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "service",
        "buyer",
        "seller",
        "status",
        "created_at",
        "updated_at",
    )
    list_filter = ("status", "created_at", "updated_at")
    search_fields = (
        "service__title",
        "buyer__username",
        "seller__username",
        "buyer_requirements",
        "seller_update_message",
        "buyer_response_note",
    )
    ordering = ("-created_at",)
    readonly_fields = (
        "created_at",
        "updated_at",
        "seller_updated_at",
        "buyer_reviewed_at",
        "completed_at",
    )