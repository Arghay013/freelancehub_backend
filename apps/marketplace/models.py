from django.db import models
from django.contrib.auth.models import User

class Service(models.Model):
    CATEGORY_CHOICES = [
        ("graphic", "Graphic Design"),
        ("writing", "Writing"),
        ("programming", "Programming"),
        ("video", "Video Editing"),
        ("marketing", "Marketing"),
    ]

    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="services")
    title = models.CharField(max_length=120)
    description = models.TextField()
    requirements = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    delivery_time_days = models.PositiveIntegerField(default=3)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Review(models.Model):
    order = models.OneToOneField("orders.Order", on_delete=models.CASCADE, related_name="review")
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews_left")
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews_received")
    rating = models.PositiveIntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.rating}/5 by {self.buyer.username}"
