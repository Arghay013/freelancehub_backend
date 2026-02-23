from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .serializers import RegisterSerializer, MeSerializer
from .tokens import make_verify_token, read_verify_token

class VerifiedTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        if not getattr(user, "profile", None) or not user.profile.is_email_verified:
            from rest_framework.exceptions import AuthenticationFailed
            raise AuthenticationFailed('Email not verified')
        return data

class VerifiedTokenObtainPairView(TokenObtainPairView):
    serializer_class = VerifiedTokenObtainPairSerializer
@extend_schema(request=RegisterSerializer, responses={201: dict})
@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    ser = RegisterSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    user = ser.save()

    token = make_verify_token(user.id)
    verify_url = f"{settings.FRONTEND_URL}/verify?token={token}"
    subject = "Verify your FreelancerHub account"
    message = f"Hi {user.username},\n\nPlease verify your email by clicking:\n{verify_url}\n\nThis link expires in 3 days."
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)

    return Response({"detail": "Registered. Please check your inbox to verify email."}, status=status.HTTP_201_CREATED)

@api_view(["GET"])
@permission_classes([AllowAny])
def verify_email(request):
    token = request.query_params.get("token", "")
    if not token:
        return Response({"detail": "Missing token"}, status=400)
    try:
        uid = read_verify_token(token)
        user = User.objects.get(id=uid)
        user.profile.is_email_verified = True
        user.profile.save()
        return Response({"detail": "Email verified. You can login now."})
    except Exception:
        return Response({"detail": "Invalid or expired token"}, status=400)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    return Response(MeSerializer(request.user).data)
