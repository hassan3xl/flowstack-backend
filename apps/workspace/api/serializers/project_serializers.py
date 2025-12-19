# serializers.py
from rest_framework import serializers
from users.api import UserSerializer
from workspace.models import Workspace, Project, Task, Comment, ProjectMember
from django.utils import timezone
from rest_framework.validators import UniqueTogetherValidator


class ProjectMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = ProjectMember
        fields = [
            "id",
            "project",
            "user",
            "user_id",
            "permission",
            "created_at",
        ]
        extra_kwargs = {
            "project": {"read_only": True},
            "user": {"read_only": True},
        }


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = [
            "id",
            "author",
            "content",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("id", "author", "created_at")


class TaskSerializer(serializers.ModelSerializer):
    started_by = serializers.CharField(
        source="started_by.profile.username", read_only=True
    )
    assigned_to = serializers.CharField(
        source="assigned_to.profile.username", read_only=True
    )
    due_date = serializers.DateField(required=False, allow_null=True)
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = "__all__"
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
            "project",
            "completed_at",
            "started_by",
        )


class ProjectSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)
    task_count = serializers.SerializerMethodField()
    completed_count = serializers.SerializerMethodField()
    created_by = serializers.CharField(
        source="created_by.profile.username", read_only=True
    )
    members = ProjectMemberSerializer(many=True, read_only=True, source="collaborators")

    class Meta:
        model = Project
        fields = [
            "id",
            "title",
            "description",
            "status",
            "task_count",
            "completed_count",
            "created_by",
            "created_at",
            "updated_at",
            "members",
            "tasks",
        ]
        read_only_fields = (
            "id",
            "created_by",
            "created_at",
            "updated_at",
            "tasks",
        )

    def get_task_count(self, obj):
        return obj.tasks.count()

    def get_completed_count(self, obj):
        return obj.tasks.filter(status=Task.StatusChoices.COMPLETED).count()


class ProjectWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "title", "description"]
        read_only_fields = ("id", "created_at", "updated_at")
