from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.exceptions import NotFound

from .models import Notification
from .serializers import NotificationSerializer

class NotificationListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def mark_read(request, pk: int):
    try:
        n = Notification.objects.get(id=pk, user=request.user)
    except Notification.DoesNotExist:
        raise NotFound("Not found")
    n.is_read = True
    n.save()
    return Response(NotificationSerializer(n).data)
