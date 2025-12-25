from django.db import models
from django.utils import timezone
import uuid

from users.models import User
from workspace.models import Workspace


class Project(models.Model):
    STATUS_CHOICES = (
        ("planning", "Planning"),
        ("active", "Active"),
        ("on_hold", "On Hold"),
        ("completed", "Completed"),
        ("archived", "Archived"),
    )

    VISIBILITY_CHOICES = (
        ('public', 'Public (Visible to Workspace)'),
        ('private', 'Private (Invite Only)'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="projects",
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="planning",
    )
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='private')

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="created_projects",
        null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "projects"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class ProjectMember(models.Model):
    PERMISSION_CHOICES = (
        ("read", "Read"),
        ("write", "Write"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="members",
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    permission = models.CharField(
        max_length=20,
        choices=PERMISSION_CHOICES,
        default="read",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("project", "user")
