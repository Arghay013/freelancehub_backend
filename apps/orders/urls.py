from django.urls import path
from .views import (
    OrderCreateView,
    BuyerOrderListView,
    SellerOrderListView,
    SellerOrderUpdateView,
    BuyerOrderReviewView,
    SellerOrderStatusUpdateView,
)

urlpatterns = [
    path("create/", OrderCreateView.as_view()),
    path("buyer/", BuyerOrderListView.as_view()),
    path("seller/", SellerOrderListView.as_view()),
    path("<int:pk>/seller-update/", SellerOrderUpdateView.as_view()),
    path("<int:pk>/buyer-review/", BuyerOrderReviewView.as_view()),
    path("<int:pk>/status/", SellerOrderStatusUpdateView.as_view()),
]