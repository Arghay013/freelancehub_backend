from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import register, verify_email, me, VerifiedTokenObtainPairView

urlpatterns = [
    path("register/", register),
    path("verify/", verify_email),
    path("token/", VerifiedTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", me),
]
