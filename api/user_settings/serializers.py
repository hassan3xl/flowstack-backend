
# serializers.py
from rest_framework import serializers
from core.models import UserSettings
from django.utils import timezone
import uuid

class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')

