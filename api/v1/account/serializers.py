# serializers.py
from rest_framework import serializers
from user_manager.models import CustomUser, UserProfile
from django.utils import timezone
import uuid

class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    username = serializers.CharField(source='profile.username', read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'username', 'avatar']
    
    def get_avatar(self, obj):
        if hasattr(obj, 'profile') and obj.profile.avatar:
            return obj.profile.avatar.url
        return None

class AccountUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', ]
    

class AccountProfileSerializer(serializers.ModelSerializer):
    user = AccountUserSerializer(read_only=True)
    avatar = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ["id", "avatar", "first_name", "last_name", "full_name", "username", "bio", "phone_number", "user", ]
        read_only_fields = ('user', 'created_at', 'updated_at')
    
    def get_avatar(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()
