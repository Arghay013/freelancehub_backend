from django.urls import path
from .views import ServiceListCreateView, ServiceRetrieveView, ReviewListCreateView

urlpatterns = [
    path("", ServiceListCreateView.as_view()),
    path("<int:pk>/", ServiceRetrieveView.as_view()),
    path("<int:service_id>/reviews/", ReviewListCreateView.as_view()),
]
