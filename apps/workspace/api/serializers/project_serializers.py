# serializers.py
from rest_framework import serializers
from users.api import UserSerializer
from workspace.models import Workspace, Project, Task, Comment, ProjectMember, WorkspaceMember
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
        
class TaskWriteSerializer(serializers.ModelSerializer):
    # We accept a UUID string for the user ID
    assign_user_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Task
        fields = "__all__"
        # We hide fields that should not be touched during creation
        read_only_fields = (
            "id", "created_at", "updated_at", "project", 
            "completed_at", "started_by", "created_by", "assigned_to"
        )

    def validate_assign_user_id(self, value):
        """
        Check if the User is a valid assignee.
        Valid = Explicit Project Member OR Workspace Admin/Owner.
        """
        if not value:
            return None

        project_id = self.context['view'].kwargs.get('project_id')
        
        # 1. Check if they are an explicit Project Member
        is_project_member = ProjectMember.objects.filter(
            project_id=project_id, 
            user_id=value
        ).exists()

        if is_project_member:
            return value

        # 2. Check if they are a Workspace Admin/Owner
        # We need to find the workspace ID first
        project = Project.objects.get(id=project_id)
        
        is_workspace_admin = WorkspaceMember.objects.filter(
            workspace=project.workspace,
            user_id=value,
            role__in=['admin', 'owner'] # Allow admins and owners
        ).exists()

        if is_workspace_admin:
            return value

        raise serializers.ValidationError("The assigned user is not a member of this project.")

    def create(self, validated_data):
        # 1. Extract the custom field
        assign_user_id = validated_data.pop('assign_user_id', None)

        # 2. Convert UUID to User instance if present
        if assign_user_id:
            validated_data['assigned_to_id'] = assign_user_id
        
        # 3. Create the task
        return super().create(validated_data)



class ProjectSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)
    task_count = serializers.SerializerMethodField()
    completed_count = serializers.SerializerMethodField()
    created_by = serializers.CharField(
        source="created_by.profile.username", read_only=True
    )
    members = ProjectMemberSerializer(many=True, read_only=True)
    user_permission = serializers.SerializerMethodField()

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
            "user_permission",
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

    
    def get_user_permission(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None

        member = obj.members.filter(user=request.user).first()
        if not member:
            return None

        return {
            "permission": member.permission,
            "joined_at": member.created_at,
        }


class ProjectWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "title", "description", "visibility"]
        read_only_fields = ("id", "created_at", "updated_at")
