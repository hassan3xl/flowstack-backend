from django.db import models
from users.models import User 
import uuid


class Workspace(models.Model):
    VISIBILITY_CHOICES = (
        ('private', 'Private'),
        ('invite', 'Invite Only'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='workspace_logos/', null=True, blank=True)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_workspaces'
    )

    visibility = models.CharField(
        max_length=10,
        choices=VISIBILITY_CHOICES,
        default='private'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name



class WorkspaceMember(models.Model):
    ROLE_CHOICES = (
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('member', 'Member'),
        ('guest', 'Guest'),
    )

    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False
    )
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='members'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='workspace_memberships'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('workspace', 'user')


class WorkspaceInvitation(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('member', 'Member'),
        ('guest', 'Guest'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='invitations'
    )
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='workspace_invites_sent'
    )

    invited_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workspace_invites_received'
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class WorkspaceChannel(models.Model):
    CHANNEL_TYPES = (
        ('chat', 'Chat'),
        ('announcement', 'Announcement'),
    )

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='channels'
    )

    name = models.CharField(max_length=100)
    channel_type = models.CharField(max_length=20, choices=CHANNEL_TYPES)
    is_private = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

# workspace/models.py

class ActivityLog(models.Model):
    ACTION_TYPES = (
        ('create_project', 'Created Project'),
        ('add_project_member', 'Added Project Member'),
        ('create_task', 'Created Task'),
        ('start_task', 'Started Task'),
        ('complete_task', 'Completed Task'),
        ('comment', 'Commented'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='activities')
    actor = models.ForeignKey(User, on_delete=models.CASCADE)
    
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    
    # We store the target name/title as a string so if the object is deleted, 
    # the log still makes sense.
    target_id = models.UUIDField(null=True, blank=True) 
    target_text = models.CharField(max_length=200) # e.g. "Fix Login Bug" or "API Project"
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.actor.username} - {self.action_type}"