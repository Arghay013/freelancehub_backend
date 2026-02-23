from django.conf import settings
from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    ROLE_SELLER = "SELLER"
    ROLE_BUYER = "BUYER"
    ROLE_CHOICES = [(ROLE_SELLER, "Seller"), (ROLE_BUYER, "Buyer")]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    is_email_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} ({self.role})"
