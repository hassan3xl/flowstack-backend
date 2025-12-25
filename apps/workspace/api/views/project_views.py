# views.py
from rest_framework import viewsets, status, generics, permissions
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from django.db import models
from workspace.permissions.project_permissions import HasProjectAccess
from workspace.models import (
    Project, 
    Task, 
    ProjectMember, 
    Workspace, 
    WorkspaceMember, 
    Comment
)
from users.models import User

from workspace.api import (
    ProjectSerializer,
    ProjectWriteSerializer,
    TaskSerializer,
    CommentSerializer,
    ProjectMemberSerializer
)
from notifications.notification_services import NotificationService
from workspace.workspace_services import (
    create_project_service,
    start_task_service, 
    create_comment_service,
    complete_task_service,
    add_project_member_service
)
from django.db.models import Q


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

        try:
            membership = WorkspaceMember.objects.get(workspace_id=workspace_id, user=user)
        except WorkspaceMember.DoesNotExist:
            return Project.objects.none()
        
        base_qs = Project.objects.filter(workspace_id=workspace_id)
        if membership.role in ['owner', 'admin']:
            return base_qs
        
        return base_qs.filter(
            Q(visibility='public') | 
            Q(members__user=user)
        ).distinct()


    def perform_create(self, serializer):
        workspace_id = self.kwargs.get("workspace_id")
        workspace = get_object_or_404(Workspace, id=workspace_id)
        user = self.request.user

        create_project_service(
            user=user,
            workspace=workspace,
            project_data=serializer.validated_data
        )

    def perform_update(self, serializer):
        workspace_id = self.kwargs.get("workspace_id")
        workspace = get_object_or_404(Workspace, id=workspace_id)
        user = self.request.user

        if not WorkspaceMember.objects.filter(workspace=workspace, user=user).exists():
            raise PermissionDenied("You are not a member of this workspace.")

        serializer.save()

        

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

    def get_queryset(self):
        project_id = self.kwargs.get("project_id")
        return ProjectMember.objects.filter(project_id=project_id).select_related('user')

    def create(self, request, *args, **kwargs):
        # 1. Permission Check
        workspace_id = self.kwargs.get("workspace_id")
        project_id = self.kwargs.get("project_id")
        
        is_admin = WorkspaceMember.objects.filter(
            workspace_id=workspace_id,
            user=request.user,
            role__in=["owner", "admin", "moderator"]
        ).exists()
        
        if not is_admin:
            raise PermissionDenied("Only admins can add members.")

        # 2. Get Data
        project = get_object_or_404(Project, id=project_id)
        
        # We manually validate using the serializer to get the 'user_id' cleanly
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Extract user_id from serializer (assuming you have user_id in write_only fields)
        # Note: If your serializer expects a full object, adjust accordingly.
        # Assuming serializer has 'user_id' field:
        user_id = serializer.validated_data.get('user_id') 
        # OR if you used PrimaryKeyRelatedField:
        target_user = serializer.validated_data.get('user') 

        if not target_user:
             # Fallback if using raw ID
             target_user = get_object_or_404(User, id=request.data.get('user_id'))

        # 3. Additional Validation
        if not WorkspaceMember.objects.filter(workspace_id=workspace_id, user=target_user).exists():
            return Response({"user": "User is not in this workspace."}, status=400)
            
        if ProjectMember.objects.filter(project=project, user=target_user).exists():
            return Response({"detail": "User is already in project."}, status=400)

        # 4. Service Call
        member = add_project_member_service(
            actor=request.user,
            project=project,
            target_user=target_user,
            role=serializer.validated_data.get('permission', 'read')
        )

        return Response(ProjectMemberSerializer(member).data, status=status.HTTP_201_CREATED)

# ----------------------- TASK ACTIONS -----------------------
class StartTaskView(APIView):
    # permission_classes = [IsAuthenticated, HasProjectAccess] # Keep your custom permission

    def post(self, request, workspace_id, project_id, task_id):
        # Validation Logic stays in View (Fast fail)
        task = get_object_or_404(Task, id=task_id, project_id=project_id, project__workspace_id=workspace_id)

        if task.status != 'pending': # Assuming 'pending' is the string value
            return Response({"detail": "Task is not in pending state."}, status=status.HTTP_400_BAD_REQUEST)
        
        if task.started_by is not None:
             return Response({"detail": "Task already started."}, status=status.HTTP_400_BAD_REQUEST)

        # Service Call
        updated_task = start_task_service(request.user, task)
        
        return Response(TaskSerializer(updated_task).data)


class CompleteTaskView(APIView):
    # permission_classes = [IsAuthenticated, HasProjectAccess]

    def post(self, request, workspace_id, project_id, task_id):
        task = get_object_or_404(Task, id=task_id, project_id=project_id)

        # Specific Logic: Only the person who started it can finish it? 
        # (Or maybe Admins too? Adjust logic as needed)
        if task.status != 'in_progress':
             return Response({"detail": "Task is not in progress."}, status=status.HTTP_400_BAD_REQUEST)
             
        if task.started_by != request.user:
            # You might want to allow Project Admins to override this check
            return Response({"detail": "You are not the user that started this task."}, status=status.HTTP_403_FORBIDDEN)

        # Service Call
        updated_task = complete_task_service(request.user, task)

        return Response(TaskSerializer(updated_task).data)


# ----------------------- COMMENTS -----------------------
class CommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # We don't need the service for GET, just standard optimization
        return Comment.objects.filter(
            task_id=self.kwargs.get("task_id")
        ).select_related('author').order_by("created_at")

    def perform_create(self, serializer):
        # Get the Task object
        task = get_object_or_404(
            Task, 
            id=self.kwargs.get("task_id"), 
            project_id=self.kwargs.get("project_id")
        )
        
        # Use Service instead of serializer.save()
        create_comment_service(
            user=self.request.user,
            task=task,
            content=serializer.validated_data['content']
        )