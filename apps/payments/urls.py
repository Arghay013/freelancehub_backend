from django.urls import path
from .views import (
    SSLCommerzInitView,
    ssl_success,
    ssl_fail,
    ssl_cancel,
)

urlpatterns = [
    path("sslcommerz/init/", SSLCommerzInitView.as_view()),

    # ✅ SSLCommerz will POST here
    path("sslcommerz/success/", ssl_success),
    path("sslcommerz/fail/", ssl_fail),
    path("sslcommerz/cancel/", ssl_cancel),
]