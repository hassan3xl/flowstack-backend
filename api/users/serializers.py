# serializers.py
from rest_framework import serializers
from core.models import CustomUser, UserProfile
from django.utils import timezone
import uuid
from api.user_projects.serializers import ProjectSerializer


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'email',  
                 'created_at', 'updated_at')
        read_only_fields = ('id', 'email',  'created_at', 'updated_at')

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
        projects = obj.projects.filter(visibility="public", is_archived=False)
        return ProjectSerializer(projects, many=True).data