from rest_framework import serializers
from core.models import CustomUser, UserProfile, Project, ProjectItem, SharedListAccess, UserSettings

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'bio', 'avatar', 'phone_number', 'email_notifications']

class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        fields = ['theme', 'language', 'items_per_page', 'default_due_date_days', 
                 'enable_email_notifications', 'enable_push_notifications', 'auto_archive_completed']

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'title', 'description', 'visibility', 'is_archived', 'created_at', 'updated_at']

class ProjectItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectItem
        fields = ['id', 'title', 'description', 'due_date', 'priority', 'status', 'completed_at']