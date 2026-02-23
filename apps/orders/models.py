from django.db import models
from django.contrib.auth.models import User

class Order(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_IN_PROGRESS = "IN_PROGRESS"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_COMPLETED, "Completed"),
    ]

    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders_made")
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders_received")
    service = models.ForeignKey("marketplace.Service", on_delete=models.CASCADE, related_name="orders")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    buyer_requirements = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Order#{self.id} {self.service.title}"
