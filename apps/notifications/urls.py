from django.urls import path
from .views import NotificationListView, mark_read

urlpatterns = [
    path("", NotificationListView.as_view()),
    path("<int:pk>/read/", mark_read),
]
