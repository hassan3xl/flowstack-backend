# workspace/serializers.py
from rest_framework import serializers
from workspace.models import Workspace, WorkspaceMember, WorkspaceInvitation, WorkspaceChannel, Project, Task, ActivityLog
from users.api.serializers.user_serializers import UserSerializer 

class DashboardMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = WorkspaceMember
        fields = ['id', 'user', 'role']

class DashboardProjectSerializer(serializers.ModelSerializer):
    # Calculate progress percentage on the fly
    progress = serializers.SerializerMethodField()
    collaborators = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'title', 'status', 'updated_at', 'progress', 'collaborators']

    def get_progress(self, obj):
        total = obj.total_tasks
        completed = obj.completed_tasks
        if total == 0: return 0
        return int((completed / total) * 100)

    def get_collaborators(self, obj):
        # Return first 3 members for the UI avatars
        members = obj.members.select_related('user')[:4]
        return [{
            "user": {
                "username": m.user.profile.username, 
                "avatar": m.user.profile.avatar.url if m.user.profile.avatar else None}
        } for m in members]

class DashboardTaskSerializer(serializers.ModelSerializer):
    project_title = serializers.CharField(source='project.title', read_only=True)
    
    class Meta:
        model = Task
        fields = ['id', 'title', 'priority', 'due_date', 'project_title', 'status']

class ActivityLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source='actor.profile.username')
    actor_avatar = serializers.ImageField(source='actor.profile.avatar', read_only=True)

    class Meta:
        model = ActivityLog
        fields = ['id', 'actor_name', 'actor_avatar', 'action_type', 'target_text', 'created_at']