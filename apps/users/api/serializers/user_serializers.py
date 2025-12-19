# serializers.py
from rest_framework import serializers
from users.models.user import User
from django.utils import timezone
import uuid

class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    username = serializers.CharField(source='profile.username', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'avatar']
    
    def get_avatar(self, obj):
        if hasattr(obj, 'profile') and obj.profile.avatar:
            return obj.profile.avatar.url
        return None

class AccountUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', ]
    