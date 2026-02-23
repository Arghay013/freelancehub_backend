from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings

@api_view(["GET"])
def health(request):
    return Response({"status": "ok", "env": settings.APP_ENV})
