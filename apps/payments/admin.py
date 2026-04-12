from django.contrib import admin
from .models import PaymentTransaction


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "tran_id", "order", "amount", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("tran_id", "order__id", "customer_name", "customer_phone")
    ordering = ("-created_at",)
    readonly_fields = (
        "raw_init_response",
        "raw_validation",
        "created_at",
        "updated_at",
    )