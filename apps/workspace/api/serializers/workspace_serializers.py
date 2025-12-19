from rest_framework import serializers
from users.models import User
from workspace.models import Workspace, WorkspaceMember, WorkspaceInvitation, WorkspaceChannel
from users.api import UserSerializer


class WorkspaceDashboardSerializer(serializers.Serializer):
    projects = serializers.IntegerField()
    tasks = serializers.IntegerField()
    completed_tasks = serializers.IntegerField()
    members = serializers.IntegerField()


class WorkspaceMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = WorkspaceMember
        fields = ['id', 'user', 'role', 'joined_at']


class WorkspaceSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    members = WorkspaceMemberSerializer(many=True, read_only=True)
    # logo = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()

    class Meta:
        model = Workspace
        fields = [
            'id',
            'name',
            'description',
            'owner',
            "logo",
            'visibility',
            'created_at',
            'is_owner',
            'user_role',
            'members',
        ]
        read_only_fields = ['id', 'owner', 'created_at']

    
    def get_is_owner(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.owner_id == request.user.id
        return False

    def get_user_role(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            membership = WorkspaceMember.objects.filter(
                workspace=obj,
                user=request.user
            ).first()
            return membership.role if membership else None
        return None


class CreateWorkspaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workspace
        fields = ['id', 'name', 'description', 'visibility']
        read_only_fields = ['id']

        


class CreateWorkspaceInvitationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)

    class Meta:
        model = WorkspaceInvitation
        fields = [
            'id',
            'workspace',
            'email',
            'role',
            'max_uses',
            'expires_at',
            'invite_code',
        ]
        read_only_fields = ['id', 'invite_code', 'workspace']

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "No user with this email exists."
            )
        return value

    def create(self, validated_data):
        request = self.context['request']
        email = validated_data.pop('email')
        workspace = self.context['workspace']

        if request.user.email == email:
            raise serializers.ValidationError(
                "You cannot invite yourself."
            )

        invited_user = User.objects.get(email=email)

        if WorkspaceInvitation.objects.filter(
            workspace=workspace,
            invited_user=invited_user,
        ).exists():
            raise serializers.ValidationError(
                "This user already has an active invitation."
            )

        return WorkspaceInvitation.objects.create(
            workspace=workspace,
            invited_by=request.user,
            invited_user=invited_user,
            **validated_data
        )


class UploadWorkspaceLogoSerializer(serializers.Serializer):
    icon = serializers.ImageField(required=True)

    def update(self, instance, validated_data):
        instance.icon = validated_data['icon']
        instance.save()
        return instance
