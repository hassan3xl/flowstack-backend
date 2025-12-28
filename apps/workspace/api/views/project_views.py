# views.py
from rest_framework import viewsets, status, generics, permissions
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from django.db import models
# from workspace.permissions.project_permissions import HasProjectAccess
# from workspace.permissions.workspace_permissions import IsWorkspaceMember
from workspace.permissions.permissions import (
    IsProjectCollaboratorOrWorkspaceAdmin, 
    IsTaskCollaboratorOrProjectAdmin
)

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
    TaskWriteSerializer,
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

    permission_classes = [
        IsAuthenticated, 
        IsProjectCollaboratorOrWorkspaceAdmin
    ]

    def get_serializer_class(self):
        if self.action in ["create"]:
            return ProjectWriteSerializer
        return ProjectSerializer

    def get_queryset(self):
        workspace_id = self.kwargs.get("workspace_id")
        user = self.request.user

        try:
            membership = getattr(self.request, 'workspace_memberships', None) or \
                WorkspaceMember.objects.get(workspace_id=workspace_id, user=user)
        except WorkspaceMember.DoesNotExist:
            return Project.objects.all()
        
        base_qs = Project.objects.filter(workspace_id=workspace_id)
        
        # Admins see everything
        if membership.role in ['owner', 'admin']:
            return base_qs
        
        # Members see Public + Their Projects
        return base_qs.filter(
            Q(visibility='public') | 
            Q(members__user=user)
        ).distinct()

    def perform_create(self, serializer):
        workspace_id = self.kwargs.get("workspace_id")
        workspace = get_object_or_404(Workspace, id=workspace_id)

        create_project_service(
            user=self.request.user,
            workspace=workspace,
            project_data=serializer.validated_data
        )


class TaskListCreateView(generics.ListCreateAPIView):
    permission_classes = [
        IsTaskCollaboratorOrProjectAdmin
    ]

    def get_serializer_class(self):
        # "self.action" does not exist in Generic Views, use request.method
        if self.request.method == 'POST':
            return TaskWriteSerializer
        return TaskSerializer

    def get_queryset(self):
        # Optimization: Fetch workspace/project ONCE to validate existence, 
        # but you don't need to fetch them just to filter the tasks if you trust the IDs.
        # Ideally, validate hierarchy:
        return Task.objects.filter(
            project__id=self.kwargs["project_id"], 
            project__workspace_id=self.kwargs["workspace_id"]
        ).order_by("-created_at")

    def perform_create(self, serializer):
        workspace_id = self.kwargs.get("workspace_id")
        project_id = self.kwargs.get("project_id")
        user = self.request.user

        # Fetch project with validation
        project = get_object_or_404(Project, id=project_id, workspace_id=workspace_id)

        # 1. Save the task first (to get an ID and Object)
        task = serializer.save(project=project, created_by=user)

        # 2. Notifications (Refined)
        # We perform this AFTER save to ensure the task actually exists
        members = project.members.all().select_related('user') # Optimization
        recipient_users = [m.user for m in members if m.user != user] # Exclude self
        
        if recipient_users:
            NotificationService.send_bulk_notification(
                recipients=recipient_users,
                actor=user,
                title="New Task Added",
                message=f"New task '{task.title}' added to project '{project.title}'.",
                target_obj=task, # Point to the task, not the project
                category='task_added',
            )

class TaskRetrieveUpdateView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    permission_classes = [
        IsAuthenticated,
        IsTaskCollaboratorOrProjectAdmin
    ]

    lookup_field = "id"
    lookup_url_kwarg = "task_id"

    def get_queryset(self):
        workspace_id = self.kwargs.get("workspace_id")
        project_id = self.kwargs.get("project_id")
        user = self.request.user

        workspace = get_object_or_404(Workspace, id=workspace_id)
        project = get_object_or_404(Project, id=project_id, workspace=workspace)


        return Task.objects.filter(project=project)

    def perform_update(self, serializer):
        workspace_id = self.kwargs.get("workspace_id")
        project_id = self.kwargs.get("project_id")
        task_id = self.kwargs.get("task_id")
        user = self.request.user

        workspace = get_object_or_404(Workspace, id=workspace_id)
        project = get_object_or_404(Project, id=project_id, workspace=workspace)
        task = get_object_or_404(Task, id=task_id, project=project)


        serializer.save(project=project)

    def perform_destroy(self, instance):
        workspace_id = self.kwargs.get("workspace_id")
        project_id = self.kwargs.get("project_id")
        user = self.request.user

        workspace = get_object_or_404(Workspace, id=workspace_id)
        project = get_object_or_404(Project, id=project_id, workspace=workspace)


        instance.delete()


# ----------------------- PROJECT MEMBERS -----------------------
class ProjectMemberView(generics.ListCreateAPIView):
    serializer_class = ProjectMemberSerializer
    permission_classes = [
        IsAuthenticated,
        IsProjectCollaboratorOrWorkspaceAdmin    
    ]

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
    permission_classes = [
        IsAuthenticated, 
        IsProjectCollaboratorOrWorkspaceAdmin
    ]


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
    permission_classes = [
        IsAuthenticated, 
        IsProjectCollaboratorOrWorkspaceAdmin
    ]


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
    permission_classes = [
        IsAuthenticated, 
        IsProjectCollaboratorOrWorkspaceAdmin
    ]
    
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