# # serializers.py
from rest_framework import serializers
from notifications.models import Notification
from rest_framework import serializers
from users.api.serializers.user_serializers import UserSerializer

class NotificationSerializer(serializers.ModelSerializer):
    actor = UserSerializer(read_only=True)
    
    # Helper fields for frontend routing
    target_type = serializers.CharField(source='content_type.model', read_only=True)
    target_id = serializers.UUIDField(source='object_id', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 
            'actor', 
            'title', 
            'message', 
            'category', 
            'type', 
            'is_read', 
            'created_at',
            'target_type', # e.g., "task", "project", "comment"
            'target_id',   # Use this ID to link to the page (e.g. /tasks/{id})
        ]