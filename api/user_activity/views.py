# views.py
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from core.models import (

    ActivityLog,
)
from .serializers import (
   
    ActivityLogSerializer,
)
from core.permissions import IsOwnerOrSharedReadOnly, IsOwnerOrSharedWrite


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ActivityLog.objects.filter(user=self.request.user)