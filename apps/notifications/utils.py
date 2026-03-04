from django.db import transaction
from .models import Notification

def notify(user, ntype: str, message: str):
    """
    Create a notification for a user.
    - Works with custom AUTH_USER_MODEL
    - Safe for None user
    - Always stores strings
    """
    if not user:
        return None

    ntype = str(ntype or "NOTIFICATION")[:50]
    message = str(message or "").strip()

    if not message:
        return None

    # atomic to avoid partial issues
    with transaction.atomic():
        return Notification.objects.create(
            user=user,
            ntype=ntype,
            message=message
        )