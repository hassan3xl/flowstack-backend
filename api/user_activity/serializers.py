
# serializers.py
from rest_framework import serializers
from core.models import ActivityLog
import uuid

class ActivityLogSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = ActivityLog
        fields = '__all__'
        read_only_fields = ('id', 'user', 'created_at')