from django.shortcuts import render
from rest_framework import permissions

from users.serializers import RegistrationSerializer


class RegisterAPIView():
    serializer_class = RegistrationSerializer
    permission_classes = [permissions.AllowAny]

    
