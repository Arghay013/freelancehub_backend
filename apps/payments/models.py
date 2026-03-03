from django.db import models
from apps.orders.models import Order

class PaymentTransaction(models.Model):
    STATUS_INITIATED = "INITIATED"
    STATUS_PAID = "PAID"
    STATUS_FAILED = "FAILED"
    STATUS_CANCELLED = "CANCELLED"

    STATUS_CHOICES = [
        (STATUS_INITIATED, "Initiated"),
        (STATUS_PAID, "Paid"),
        (STATUS_FAILED, "Failed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    tran_id = models.CharField(max_length=80, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    customer_name = models.CharField(max_length=120)
    customer_phone = models.CharField(max_length=40)
    customer_address = models.TextField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_INITIATED)
    raw_init_response = models.JSONField(null=True, blank=True)
    raw_validation = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.tran_id} ({self.status})"