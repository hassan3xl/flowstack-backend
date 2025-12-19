# views.py
from rest_framework import viewsets, status, generics, permissions
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from django.db import models
from workspace.utils.permissions.project_permissions import HasProjectAccess
from workspace.models import Project, Task, ProjectMember, Workspace, WorkspaceMember
from users.models import User

from workspace.api import (
    ProjectSerializer,
    ProjectWriteSerializer,
    TaskSerializer,
    CommentSerializer,
    ProjectMemberSerializer
)
from notifications.services import NotificationService


# ----------------------- PROJECT -----------------------
class ProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ["create"]:
            return ProjectWriteSerializer
        return ProjectSerializer

    def get_queryset(self):
        workspace_id = self.kwargs.get("workspace_id")
        user = self.request.user

        workspace = get_object_or_404(Workspace, id=workspace_id)

        if not WorkspaceMember.objects.filter(workspace=workspace, user=user).exists():
            raise PermissionDenied("You are not a member of this workspace.")

        return Project.objects.filter(workspace=workspace).order_by("-created_at")

    def perform_create(self, serializer):
        workspace_id = self.kwargs.get("workspace_id")
        workspace = get_object_or_404(Workspace, id=workspace_id)
        user = self.request.user

        if not WorkspaceMember.objects.filter(workspace=workspace, user=user).exists():
            raise PermissionDenied("You are not a member of this workspace.")

        serializer.save(workspace=workspace, created_by=user)

    def perform_update(self, serializer):
        workspace_id = self.kwargs.get("workspace_id")
        workspace = get_object_or_404(Workspace, id=workspace_id)
        user = self.request.user

        if not WorkspaceMember.objects.filter(workspace=workspace, user=user).exists():
            raise PermissionDenied("You are not a member of this workspace.")

        serializer.save(workspace=workspace)

    def perform_destroy(self, instance):
        workspace_id = self.kwargs.get("workspace_id")
        workspace = get_object_or_404(Workspace, id=workspace_id)
        user = self.request.user

        if not WorkspaceMember.objects.filter(workspace=workspace, user=user).exists():
            raise PermissionDenied("You are not a member of this workspace.")

        instance.delete()


# ----------------------- TASKS -----------------------
class TaskListCreateView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        workspace_id = self.kwargs.get("workspace_id")
        project_id = self.kwargs.get("project_id")
        user = self.request.user

        workspace = get_object_or_404(Workspace, id=workspace_id)
        project = get_object_or_404(Project, id=project_id, workspace=workspace)

        if not WorkspaceMember.objects.filter(workspace=workspace, user=user).exists():
            raise PermissionDenied("You are not a member of this workspace.")

        return Task.objects.filter(project=project).order_by("-created_at")

    def perform_create(self, serializer):
        workspace_id = self.kwargs.get("workspace_id")
        project_id = self.kwargs.get("project_id")
        user = self.request.user

        workspace = get_object_or_404(Workspace, id=workspace_id)
        project = get_object_or_404(Project, id=project_id, workspace=workspace)

        if not WorkspaceMember.objects.filter(workspace=workspace, user=user).exists():
            raise PermissionDenied("You are not a member of this workspace.")

        # Send notifications to all project members
        members = [m.user for m in project.members.all()]
        NotificationService.send_bulk_notification(
            users=members,
            title=f"New Task Added",
            message=f"A new task has been added to project '{project.title}'.",
            channels=["in_app", "email"]
        )

        serializer.save(project=project, created_by=user)


class TaskRetrieveUpdateView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"
    lookup_url_kwarg = "task_id"

    def get_queryset(self):
        workspace_id = self.kwargs.get("workspace_id")
        project_id = self.kwargs.get("project_id")
        user = self.request.user

        workspace = get_object_or_404(Workspace, id=workspace_id)
        project = get_object_or_404(Project, id=project_id, workspace=workspace)

        if not WorkspaceMember.objects.filter(workspace=workspace, user=user).exists():
            raise PermissionDenied("You are not a member of this workspace.")

        return Task.objects.filter(project=project)

    def perform_update(self, serializer):
        workspace_id = self.kwargs.get("workspace_id")
        project_id = self.kwargs.get("project_id")
        task_id = self.kwargs.get("task_id")
        user = self.request.user

        workspace = get_object_or_404(Workspace, id=workspace_id)
        project = get_object_or_404(Project, id=project_id, workspace=workspace)
        task = get_object_or_404(Task, id=task_id, project=project)

        if not WorkspaceMember.objects.filter(workspace=workspace, user=user).exists():
            raise PermissionDenied("You are not a member of this workspace.")

        serializer.save(project=project)

    def perform_destroy(self, instance):
        workspace_id = self.kwargs.get("workspace_id")
        project_id = self.kwargs.get("project_id")
        user = self.request.user

        workspace = get_object_or_404(Workspace, id=workspace_id)
        project = get_object_or_404(Project, id=project_id, workspace=workspace)

        if not WorkspaceMember.objects.filter(workspace=workspace, user=user).exists():
            raise PermissionDenied("You are not a member of this workspace.")

        instance.delete()


# ----------------------- PROJECT MEMBERS -----------------------
class ProjectMemberView(generics.ListCreateAPIView):
    serializer_class = ProjectMemberSerializer
    permission_classes = [IsAuthenticated]

    def get_project(self):
        workspace_id = self.kwargs.get("workspace_id")
        project_id = self.kwargs.get("project_id")

        return get_object_or_404(Project, id=project_id, workspace_id=workspace_id)

    def check_requester_permissions(self, workspace_id):
        allowed = WorkspaceMember.objects.filter(
            workspace_id=workspace_id,
            user=self.request.user,
            role__in=["owner", "admin", "moderator"]
        ).exists()
        if not allowed:
            raise PermissionDenied(
                "You must be an Admin, Owner, or Moderator to manage project members."
            )

    def get_queryset(self):
        project = self.get_project()
        self.check_requester_permissions(project.workspace_id)
        return ProjectMember.objects.filter(project=project)

    def perform_create(self, serializer):
        project = self.get_project()
        self.check_requester_permissions(project.workspace_id)

        user_id = serializer.validated_data.pop("user_id")
        target_user = get_object_or_404(User, id=user_id)

        # Must be workspace member
        if not WorkspaceMember.objects.filter(workspace_id=project.workspace_id, user=target_user).exists():
            raise ValidationError({"user": "Selected user is not a member of this workspace."})

        if ProjectMember.objects.filter(project=project, user=target_user).exists():
            raise ValidationError({"detail": "User is already a project member."})

        serializer.save(project=project, user=target_user)


# ----------------------- TASK ACTIONS -----------------------
class StartTaskView(APIView):
    permission_classes = [IsAuthenticated, HasProjectAccess]

    def post(self, request, workspace_id, project_id, task_id):
        user = request.user
        workspace = get_object_or_404(Workspace, id=workspace_id)
        project = get_object_or_404(Project, id=project_id, workspace=workspace)
        task = get_object_or_404(Task, id=task_id, project=project)

        if task.status != Task.StatusChoices.PENDING or task.started_by is not None:
            return Response({"detail": "Task is not available to start."}, status=status.HTTP_400_BAD_REQUEST)

        task.started_by = user
        task.status = Task.StatusChoices.IN_PROGRESS
        task.save()

        serializer = TaskSerializer(task)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CompleteTaskView(APIView):
    permission_classes = [IsAuthenticated, HasProjectAccess]

    def post(self, request, workspace_id, project_id, task_id):
        user = request.user
        workspace = get_object_or_404(Workspace, id=workspace_id)
        project = get_object_or_404(Project, id=project_id, workspace=workspace)
        task = get_object_or_404(Task, id=task_id, project=project)

        if task.status != Task.StatusChoices.IN_PROGRESS or task.started_by != user:
            return Response({"detail": "You are not the user that started this task."}, status=status.HTTP_400_BAD_REQUEST)

        task.status = Task.StatusChoices.COMPLETED
        task.completed_at = timezone.now()
        task.save()

        serializer = TaskSerializer(task)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ----------------------- COMMENTS -----------------------
class CommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = "task_id"

    def get_queryset(self):
        workspace_id = self.kwargs.get("workspace_id")
        project_id = self.kwargs.get("project_id")
        task_id = self.kwargs.get("task_id")
        workspace = get_object_or_404(Workspace, id=workspace_id)
        project = get_object_or_404(Project, id=project_id, workspace=workspace)
        task = get_object_or_404(Task, id=task_id, project=project)
        return task.comments.all().order_by("created_at")

    def perform_create(self, serializer):
        user = self.request.user
        workspace_id = self.kwargs.get("workspace_id")
        project_id = self.kwargs.get("project_id")
        task_id = self.kwargs.get("task_id")

        workspace = get_object_or_404(Workspace, id=workspace_id)
        project = get_object_or_404(Project, id=project_id, workspace=workspace)
        task = get_object_or_404(Task, id=task_id, project=project)

        serializer.save(author=user, project_item=task)
