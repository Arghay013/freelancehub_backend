from django.urls import path
from .views import *

urlpatterns = [
    path("services/", ServiceListCreateView.as_view()),
    path("services/mine/", MyServiceListView.as_view()),
    path("services/<int:pk>/", ServiceRetrieveView.as_view()),
    path("services/<int:pk>/edit/", ServiceUpdateDeleteView.as_view()),
]