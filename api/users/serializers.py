# serializers.py
from rest_framework import serializers
from core.models import CustomUser, UserProfile
from django.utils import timezone
import uuid


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'email',  
                 'created_at', 'updated_at')
        read_only_fields = ('id', 'email',  'created_at', 'updated_at')

class CustomUserSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'fullname', 'avatar']

    def get_fullname(self, obj):
        # Get fullname from UserProfile if it exists
        if hasattr(obj, 'profile'):
            return f"{obj.profile.first_name} {obj.profile.last_name}".strip()
        return obj.email  # fallback to email if no profile
    
    def get_avatar(self, obj):
        if hasattr(obj, 'profile') and obj.profile.avatar:
            return obj.profile.avatar.url
        return None

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    avatar_url = serializers.ImageField(source='avatar')

    class Meta:
        model = UserProfile
        fields = ["id", "avatar_url", 'email', "first_name", "last_name", "bio", "phone_number" ]
        read_only_fields = ('user', 'created_at', 'updated_at')


class UserPublicSerializer(serializers.ModelSerializer):
    projects = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser;
        fields = ["id", "email", "projects"]

    def get_projects(self, obj):
        from api.user_projects.serializers import ProjectSerializer

        projects = obj.projects.filter(visibility="public", is_archived=False)
        return ProjectSerializer(projects, many=True).data