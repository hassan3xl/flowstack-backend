# api/views.py (enhanced)
from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from rest_framework import generics, views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from notifications.models import Notification
from notifications.api import NotificationSerializer

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Return unread first, then newest
        return Notification.objects.filter(recipient=self.request.user).order_by('is_read', '-created_at')

class MarkNotificationReadView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            # Ensure user can only mark THEIR OWN notifications
            notification = Notification.objects.get(pk=pk, recipient=request.user)
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save()
            return Response({"status": "marked as read"})
        except Notification.DoesNotExist:
            return Response({"error": "Notification not found"}, status=404)

class MarkAllReadView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(
            is_read=True, 
            read_at=timezone.now()
        )
        return Response({"status": "all marked as read"})