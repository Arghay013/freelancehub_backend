from .models import Notification

def notify(user, ntype: str, message: str):
    Notification.objects.create(user=user, ntype=ntype, message=message)
