# views.py
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.shortcuts import get_object_or_404
from django.db.models import Q
from core.models import (
    SharedListAccess,
    UserSettings,
)
from .serializers import (
    UserSettingsSerializer,
)



# class UserSettingsViewSet(viewsets.ModelViewSet):
#     serializer_class = UserSettingsSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def get_queryset(self):
#         return UserSettings.objects.filter(user=self.request.user)

#     def get_object(self):
#         return get_object_or_404(UserSettings, user=self.request.user)


class UserSettingsView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        settings, created = UserSettings.objects.get_or_create(user=self.request.user)
        return settings