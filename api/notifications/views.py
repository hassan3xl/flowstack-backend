# api/views.py (enhanced)
from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from notifications.models import Notification, UserNotificationPreference
from .serializers import (
    NotificationListSerializer
    # NotificationCreateSerializer,
    # NotificationUpdateSerializer, BulkNotificationUpdateSerializer,
    # UserNotificationPreferenceSerializer, NotificationStatsSerializer,
    # UnreadCountSerializer, NotificationResponseSerializer
)

class NotificationsList(generics.ListAPIView):
    serializer_class = NotificationListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


# class UserNotificationPreferenceViewSet():
#     pass

# class NotificationViewSet(viewsets.ModelViewSet):
#     permission_classes = [IsAuthenticated]
    
#     def get_queryset(self):
#         return Notification.objects.filter(user=self.request.user)
    
#     def get_serializer_class(self):
#         if self.action == 'create':
#             return NotificationCreateSerializer
#         elif self.action in ['update', 'partial_update']:
#             return NotificationUpdateSerializer
#         return NotificationListSerializer
    
#     def create(self, request, *args, **kwargs):
#         """Create a new notification"""
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         notification = serializer.save()
        
#         response_serializer = NotificationResponseSerializer({
#             'success': True,
#             'message': 'Notification created successfully',
#             'notification_id': notification.id
#         })
#         return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
#     @action(detail=False, methods=['get'])
#     def stats(self, request):
#         """Get notification statistics"""
#         user_notifications = self.get_queryset()
        
#         # Calculate stats
#         total = user_notifications.count()
#         unread = user_notifications.filter(is_read=False).count()
#         read = total - unread
        
#         # Category distribution
#         by_category = user_notifications.values('category').annotate(
#             count=Count('id')
#         ).order_by('-count')
#         category_dict = {item['category'] or 'uncategorized': item['count'] for item in by_category}
        
#         # Priority distribution
#         by_priority = user_notifications.values('priority').annotate(
#             count=Count('id')
#         ).order_by('-count')
#         priority_dict = {item['priority']: item['count'] for item in by_priority}
        
#         # Recent notifications (last 7 days)
#         recent_count = user_notifications.filter(
#             created_at__gte=timezone.now() - timedelta(days=7)
#         ).count()
        
#         stats_data = {
#             'total': total,
#             'unread': unread,
#             'read': read,
#             'by_category': category_dict,
#             'by_priority': priority_dict,
#             'recent_count': recent_count
#         }
        
#         serializer = NotificationStatsSerializer(stats_data)
#         return Response(serializer.data)
    
#     @action(detail=False, methods=['get'])
#     def unread_count(self, request):
#         """Get unread notification count"""
#         unread_count = self.get_queryset().filter(is_read=False).count()
#         total_count = self.get_queryset().count()
#         unread_urgent = self.get_queryset().filter(
#             is_read=False, 
#             priority='urgent'
#         ).count()
        
#         serializer = UnreadCountSerializer({
#             'unread_count': unread_count,
#             'total_count': total_count,
#             'unread_urgent': unread_urgent
#         })
#         return Response(serializer.data)
    
#     @action(detail=False, methods=['post'])
#     def bulk_update(self, request):
#         """Bulk update notifications"""
#         serializer = BulkNotificationUpdateSerializer(
#             data=request.data,
#             context={'request': request}
#         )
#         serializer.is_valid(raise_exception=True)
        
#         data = serializer.validated_data
#         notification_ids = data['notification_ids']
#         action_type = data['action']
        
#         notifications = self.get_queryset().filter(id__in=notification_ids)
        
#         if action_type == 'mark_read':
#             notifications.update(is_read=True)
#             message = f"{len(notification_ids)} notifications marked as read"
#         elif action_type == 'mark_unread':
#             notifications.update(is_read=False)
#             message = f"{len(notification_ids)} notifications marked as unread"
#         elif action_type == 'delete':
#             count, _ = notifications.delete()
#             message = f"{count} notifications deleted"
        
#         response_serializer = NotificationResponseSerializer({
#             'success': True,
#             'message': message,
#             'notifications_affected': len(notification_ids)
#         })
#         return Response(response_serializer.data)