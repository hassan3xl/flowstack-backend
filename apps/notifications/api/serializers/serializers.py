# # serializers.py
from rest_framework import serializers
from notifications.models import Notification, NotificationTemplate, UserNotificationPreference, NotificationChannel, NotificationPriority

class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'name', 'subject', 'message', 'html_message', 
            'channels', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class NotificationListSerializer(serializers.ModelSerializer):
    # user = UserProfileSerializer(read_only=True)
    template = NotificationTemplateSerializer(read_only=True)
    
    # Computed fields
    channels_list = serializers.SerializerMethodField()
    time_since = serializers.SerializerMethodField()
    is_urgent = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'template', 'title', 'message', 'html_message',
            'channels', 'channels_list', 'priority', 'is_read', 'is_sent',
            'category', 'action_url', 'time_since', 'is_urgent',
            'created_at'
        ]
        read_only_fields = ['created_at', ]
    
    def get_channels_list(self, obj):
        """Convert comma-separated channels to list"""
        return obj.channels.split(',') if obj.channels else []
    
    def get_time_since(self, obj):
        """Human-readable time since creation"""
        from django.utils import timezone
        from django.utils.timesince import timesince
        
        if obj.created_at:
            return timesince(obj.created_at)
        return None
    
    def get_is_urgent(self, obj):
        """Check if notification is urgent"""
        return obj.priority == NotificationPriority.URGENT
