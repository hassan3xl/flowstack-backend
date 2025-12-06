# serializers.py
from rest_framework import serializers
from ..users.serializers import CustomUserSerializer
from project_manager.models import Project, ProjectItem, Comment
from django.utils import timezone


class CommentSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = [
            "id",
            "author",
            "content",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ('id', 'author', 'created_at')


class ProjectItemSerializer(serializers.ModelSerializer):
    is_overdue = serializers.SerializerMethodField()
    started_by = serializers.CharField(source='started_by.profile.username', read_only=True)
    assigned_to = serializers.CharField(source='assigned_to.profile.username', read_only=True)
    comments = CommentSerializer(many=True, read_only=True) 
    
    class Meta:
        model = ProjectItem
        fields = '__all__'
        read_only_fields = (
            'id', 'created_at', 'updated_at', "project", 
            'completed_at', 'started_by'
        )
            
    def get_is_overdue(self, obj):
        if obj.due_date and obj.status != ProjectItem.StatusChoices.COMPLETED:
            return obj.due_date < timezone.now()
        return False

class ProjectSerializer(serializers.ModelSerializer):
    project_items = ProjectItemSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()
    completed_count = serializers.SerializerMethodField()
    created_by = serializers.CharField(source='created_by.profile.username', read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'title', 'description', 'status', 'item_count', 'completed_count', 
                  'created_by', 'created_at', 'updated_at', 'project_items']
        read_only_fields = ("id", 'created_by', "created_at", "updated_at", 'project_items')

    def get_item_count(self, obj):
        return obj.project_items.count()

    def get_completed_count(self, obj):
        return obj.project_items.filter(status=ProjectItem.StatusChoices.COMPLETED).count()


class ProjectWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'title', 'description',  ]
        read_only_fields = ("id", "created_at", "updated_at")

