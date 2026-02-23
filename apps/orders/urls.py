from django.urls import path
from .views import OrderCreateView, BuyerOrderListView, SellerOrderListView, SellerOrderStatusUpdateView

urlpatterns = [
    path("create/", OrderCreateView.as_view()),
    path("buyer/", BuyerOrderListView.as_view()),
    path("seller/", SellerOrderListView.as_view()),
    path("<int:pk>/status/", SellerOrderStatusUpdateView.as_view()),
]
