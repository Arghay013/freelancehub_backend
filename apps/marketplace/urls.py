from django.urls import path
from .views import (
    ServiceListCreateView,
    ServiceRetrieveView,
    ReviewListCreateView,
    MyServiceListView,
    ServiceManageView,
)

urlpatterns = [
    path("", ServiceListCreateView.as_view()),                # GET list, POST create
    path("mine/", MyServiceListView.as_view()),              # GET seller's own services
    path("<int:pk>/", ServiceRetrieveView.as_view()),         # GET single public service
    path("<int:pk>/manage/", ServiceManageView.as_view()),    # PATCH/DELETE seller only
    path("<int:service_id>/reviews/", ReviewListCreateView.as_view()),
]