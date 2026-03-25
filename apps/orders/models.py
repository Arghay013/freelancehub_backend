from django.db import models
from django.contrib.auth.models import User


class Order(models.Model):
    STATUS_REQUESTED = "REQUESTED"
    STATUS_SELLER_UPDATED = "SELLER_UPDATED"
    STATUS_CHANGES_REQUESTED = "CHANGES_REQUESTED"
    STATUS_AWAITING_PAYMENT = "AWAITING_PAYMENT"
    STATUS_IN_PROGRESS = "IN_PROGRESS"
    STATUS_COMPLETED = "COMPLETED"

    STATUS_CHOICES = [
        (STATUS_REQUESTED, "Requested"),
        (STATUS_SELLER_UPDATED, "Seller Updated"),
        (STATUS_CHANGES_REQUESTED, "Changes Requested"),
        (STATUS_AWAITING_PAYMENT, "Awaiting Payment"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_COMPLETED, "Completed"),
    ]

    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders_made")
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders_received")
    service = models.ForeignKey("marketplace.Service", on_delete=models.CASCADE, related_name="orders")

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_REQUESTED)
    buyer_requirements = models.TextField(blank=True)
    seller_update_message = models.TextField(blank=True)
    buyer_response_note = models.TextField(blank=True)
    seller_updated_at = models.DateTimeField(null=True, blank=True)
    buyer_reviewed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Order#{self.id} {self.service.title}"