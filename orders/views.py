from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated


class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]


