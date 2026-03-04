from django.conf import settings
from django.db import models

class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    ntype = models.CharField(max_length=50)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        # user model custom হলেও safe
        uname = getattr(self.user, "username", None) or getattr(self.user, "email", "user")
        return f"{uname}: {self.ntype}"