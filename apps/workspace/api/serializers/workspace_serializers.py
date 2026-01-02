from rest_framework import serializers
from users.models import User
from workspace.models import Workspace, WorkspaceMember, WorkspaceInvitation, WorkspaceChannel
from users.api import UserSerializer
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from notifications.notification_services import NotificationService

User = get_user_model()



class UploadWorkspaceLogoSerializer(serializers.ModelSerializer):
    logo = serializers.ImageField(required=True)

    class Meta:
        model = Workspace
        fields = ['logo']

    def update(self, instance, validated_data):
        instance.logo = validated_data.get('logo', instance.logo)
        instance.save()
        return instance

    def validate_logo(self, value):
        if value.size > 2 * 1024 * 1024:
            raise serializers.ValidationError("Logo must be under 2MB.")
        return value


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
    logo = serializers.SerializerMethodField()
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

    def get_logo(self, obj):
        if obj.logo:
            return obj.logo.url
        return None


class CreateWorkspaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workspace
        fields = ['id', 'name', 'description', 'visibility']
        read_only_fields = ['id']


class WorkspaceInvitationSerializer(serializers.ModelSerializer):
    invited_user = UserSerializer(read_only=True)
    invited_by = UserSerializer(read_only=True)
    workspace = WorkspaceSerializer(read_only=True)

    class Meta:
        model = WorkspaceInvitation
        fields = [
            'id',
            'workspace',
            'invited_user',
            'invited_by',
            'role',
            'expires_at',
        ]
        read_only_fields = ['id', 'workspace']


class CreateWorkspaceInvitationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)  # Accept email as input

    class Meta:
        model = WorkspaceInvitation
        fields = [
            'id',
            'email',         # Input field
            'role',
            'expires_at',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def validate(self, attrs):
        email = attrs.get('email')
        workspace = self.context['workspace']
        
        # 1. Check if user exists
        try:
            invited_user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "User with this email does not exist."})

        # 2. Check if you are inviting yourself
        if self.context['request'].user == invited_user:
            raise serializers.ValidationError({"email": "You cannot invite yourself."})

        # 3. Check if user is ALREADY a member
        if WorkspaceMember.objects.filter(workspace=workspace, user=invited_user).exists():
            raise serializers.ValidationError({"email": "User is already a member of this workspace."})

        # 4. Check if invite ALREADY exists
        # Since rejection deletes the invite, simply checking .exists() handles the "re-invite" logic.
        if WorkspaceInvitation.objects.filter(workspace=workspace, invited_user=invited_user).exists():
            raise serializers.ValidationError({"email": "This user already has a pending invitation."})

        # Store the resolved user object in attrs to use in create()
        attrs['invited_user'] = invited_user
        return attrs

    def create(self, validated_data):
        # Remove fields that aren't directly on the model or were helper fields
        email = validated_data.pop('email')
        invited_user = validated_data.pop('invited_user')
        
        # LOGIC FOR DEADLINE:
        # If admin didn't provide a date, system assigns 7 days automatically
        if not validated_data.get('expires_at'):
            validated_data['expires_at'] = timezone.now() + timedelta(days=7)

        NotificationService.send_notification(
            actor=self.context['request'].user,
            recipient=invited_user,
            title="Workspace Invitation",
            message=f"You have been invited to join workspace '{self.context['workspace'].name}'.",
            target_obj=self.context['workspace'],
        )

        # Create the instance
        # Note: 'workspace' and 'invited_by' are passed via serializer.save() in the view
        return WorkspaceInvitation.objects.create(
            invited_user=invited_user,
            **validated_data
        )

