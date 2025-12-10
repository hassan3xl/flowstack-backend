from rest_framework import viewsets, status, generics, permissions
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from project_manager.models import Project, ProjectItem, ProjectCollaborator
from server_manager.models import Server, ServerMember
from user_manager.models import CustomUser
from rest_framework.exceptions import PermissionDenied, ValidationError
from .serializers import (
    ProjectSerializer,
    ProjectWriteSerializer,
    ProjectItemSerializer,
    CommentSerializer,
    CollaboratorSerializer
)
from ..utils.permissions.project_permissions import HasProjectAccess
from ..utils.permissions.server_permissions import (
    IsServerOwner,
    IsServerAdmin,
    IsServerAdminOrMod

)
from datetime import timezone
from notification_manager.services import NotificationService


class ProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ["create"]:
            return ProjectWriteSerializer
        return ProjectSerializer

    def get_queryset(self):
        server_id = self.kwargs.get("server_id")
        user = self.request.user

        server = get_object_or_404(Server, id=server_id)

        if not ServerMember.objects.filter(server=server, user=user).exists():
            return Project.objects.none()

        return Project.objects.filter(server=server).order_by("-created_at")

    # ✅ CREATE
    def perform_create(self, serializer):
        server_id = self.kwargs.get("server_id")
        server = get_object_or_404(Server, id=server_id)
        user = self.request.user

        if not ServerMember.objects.filter(server=server, user=user).exists():
            raise PermissionDenied("You are not a member of this server.")

        

        serializer.save(server=server, created_by=user)

    # ✅ UPDATE (EDIT)
    def perform_update(self, serializer):
        server_id = self.kwargs.get("server_id")
        server = get_object_or_404(Server, id=server_id)
        user = self.request.user

        if not ServerMember.objects.filter(server=server, user=user).exists():
            raise PermissionDenied("You are not a member of this server.")

        serializer.save(server=server)

    # ✅ DELETE
    def perform_destroy(self, instance):
        server_id = self.kwargs.get("server_id")
        server = get_object_or_404(Server, id=server_id)
        user = self.request.user

        if not ServerMember.objects.filter(server=server, user=user).exists():
            raise PermissionDenied("You are not a member of this server.")

        instance.delete()


class ProjectItemListCreateView(generics.ListCreateAPIView):
    serializer_class = ProjectItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        server_id = self.kwargs.get("server_id")
        project_id = self.kwargs.get("project_id")
        user = self.request.user

        server = get_object_or_404(Server, id=server_id)
        project = get_object_or_404(Project, id=project_id, server=server)

        # User must be member
        if not ServerMember.objects.filter(server=server, user=user).exists():
            raise PermissionDenied("You are not a member of this server.")

        return ProjectItem.objects.filter(project=project).order_by("-created_at")
    
    def perform_create(self, serializer):
        server_id = self.kwargs.get("server_id")
        project_id = self.kwargs.get("project_id")
        user = self.request.user

        server = get_object_or_404(Server, id=server_id)
        project = get_object_or_404(Project, id=project_id, server=server)


        # User must be member
        if not ServerMember.objects.filter(server=server, user=user).exists():
            raise PermissionDenied("You are not a member of this server.")
        
        title = f"New Task Added"
        message = f"A new task '{project.project_items.name}' has been added to the project '{project.title}'."

        # Get all users related to the project
        collaborators = [access.user for access in project.collaborators.all()]
        all_recipients = list(set(collaborators))
 
        # Send notifications to everyone
        NotificationService.send_bulk_notification(
            users=all_recipients,
            title=title,
            message=message,
            channels=["in_app", "email"]
        )

        serializer.save(project=project, created_by=user)

class ProjectItemRetriveUpdateView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProjectItemSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"
    lookup_url_kwarg = "item_id"

    def get_queryset(self):
        server_id = self.kwargs.get("server_id")
        project_id = self.kwargs.get("project_id")
        user = self.request.user

        server = get_object_or_404(Server, id=server_id)
        project = get_object_or_404(Project, id=project_id, server=server)

        # User must be member
        if not ServerMember.objects.filter(server=server, user=user).exists():
            raise PermissionDenied("You are not a member of this server.")

        return ProjectItem.objects.filter(project=project)

    def perform_update(self, serializer):
        server_id = self.kwargs.get("server_id")
        project_id = self.kwargs.get("project_id")
        item_id = self.kwargs.get("item_id")
        user = self.request.user

        server = get_object_or_404(Server, id=server_id)
        project = get_object_or_404(Project, id=project_id, server=server)
        item = get_object_or_404(ProjectItem, id=item_id, project=project)

        # User must be member
        if not ServerMember.objects.filter(server=server, user=user).exists():
            raise PermissionDenied("You are not a member of this server.")

        serializer.save(project=project)
    
    def perform_destroy(self, instance):
        server_id = self.kwargs.get("server_id")
        project_id = self.kwargs.get("project_id")
        user = self.request.user

        server = get_object_or_404(Server, id=server_id)
        project = get_object_or_404(Project, id=project_id, server=server)

        # User must be member
        if not ServerMember.objects.filter(server=server, user=user).exists():
            raise PermissionDenied("You are not a member of this server.")

        instance.delete()

class CollabView(generics.ListCreateAPIView):
    serializer_class = CollaboratorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_project(self):
        server_id = self.kwargs.get("server_id")
        project_id = self.kwargs.get("project_id")

        return get_object_or_404(
            Project,
            id=project_id,
            server_id=server_id
        )

    def check_requester_permissions(self, server_id):
        is_allowed = ServerMember.objects.filter(
            server_id=server_id,
            user=self.request.user,
            role__in=['owner', 'admin', 'moderator']
        ).exists()

        if not is_allowed:
            raise PermissionDenied(
                "You must be an Admin, Owner, or Moderator to manage collaborators."
            )

    def get_queryset(self):
        project = self.get_project()

        # ✅ Only server admins/mods can view collaborators
        self.check_requester_permissions(project.server_id)

        return ProjectCollaborator.objects.filter(project=project)

    def perform_create(self, serializer):
        project = self.get_project()
        self.check_requester_permissions(project.server_id)

        user_id = serializer.validated_data.pop('user_id')
        target_user = get_object_or_404(CustomUser, id=user_id)

        # ✅ Must be server member
        is_server_member = ServerMember.objects.filter(
            server_id=project.server_id,
            user=target_user
        ).exists()

        if not is_server_member:
            raise ValidationError({
                "user": "Selected user is not a member of this server."
            })

        # ✅ ✅ MANUAL DUPLICATE PROTECTION (REPLACED UNIQUE TOGETHER VALIDATOR)
        if ProjectCollaborator.objects.filter(
            project=project,
            user=target_user
        ).exists():
            raise ValidationError({
                "detail": "This user is already a collaborator on this project."
            })

        serializer.save(
            project=project,
            user=target_user
        )


class StartTaskView(APIView):
    permission_classes = [IsAuthenticated, HasProjectAccess]

    def post(self, request, project_id, item_id, server_id):
        user = request.user
        server_id = self.kwargs.get("server_id")
        project_id = self.kwargs.get("project_id")
        server = get_object_or_404(Server, id=server_id)
        project = get_object_or_404(Project, id=project_id, server=server)
        task = get_object_or_404(ProjectItem, id=item_id, project=project)

        # Check if task is free to take
        if task.status != ProjectItem.StatusChoices.PENDING or task.started_by is not None:
            return Response({"detail": "Task is not available to start."}, status=status.HTTP_400_BAD_REQUEST)

        # Assign task to user and change status
        task.started_by = user
        task.status = ProjectItem.StatusChoices.IN_PROGRESS
        task.save()

        serializer = ProjectItemSerializer(task)
        return Response(serializer.data, status=status.HTTP_200_OK)

class CompleteTaskView(APIView):
        
    def post(self, request, project_id, item_id, server_id):
        user = request.user
        server_id = self.kwargs.get("server_id")
        project_id = self.kwargs.get("project_id")
        server = get_object_or_404(Server, id=server_id)
        project = get_object_or_404(Project, id=project_id, server=server)
        task = get_object_or_404(ProjectItem, id=item_id, project=project)

        # Check if task is free to take
        if task.status != ProjectItem.StatusChoices.IN_PROGRESS or task.started_by != user:
            return Response({"detail": "Task is not available to complete."}, status=status.HTTP_400_BAD_REQUEST)

        # Assign task to user and change status
        task.status = ProjectItem.StatusChoices.COMPLETED
        task.completed_at = timezone.now()
        task.save()

        serializer = ProjectItemSerializer(task)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = "item_id"

    def perform_create(self, serializer):
        user = self.request.user
        server_id = self.kwargs.get("server_id")
        project_id = self.kwargs.get("project_id")
        item_id = self.kwargs.get("item_id")

        server = get_object_or_404(Server, id=server_id)
        project = get_object_or_404(Project, id=project_id, server=server)
        item = get_object_or_404(ProjectItem, id=item_id, project=project)

        serializer.save(author=user, project_item=item)



class ProjectRemoveUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, project_id, user_id):
        """
        Remove a user from the project.
        """
        # Fetch project, ensure owner or authorized user
        project = get_object_or_404(Project, id=project_id, owner=request.user)

        # Fetch user to be removed
        user_to_remove = get_object_or_404(CustomUser, id=user_id)

        # Prevent owner from removing themselves erroneously
        if user_to_remove == request.user:
            return Response({"error": "You cannot remove yourself."}, status=status.HTTP_400_BAD_REQUEST)

        # Remove user access
        shared_access = SharedListAccess.objects.filter(
            project=project,
            user=user_to_remove
        )
        if shared_access.exists():
            shared_access.delete()
            return Response({
                "message": f"{user_to_remove.email} has been removed from the project."
            }, status=status.HTTP_200_OK)
        else:
            return Response({"error": "User is not a collaborator of this project."}, status=status.HTTP_404_NOT_FOUND)



class ProjectArchiveToggleView(APIView):

    permission_classes = [permissions.IsAuthenticated, HasProjectAccess]

    def patch(self, request, pk):
        try:
            project = Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            return Response({"detail": "Project not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check permission
        self.check_object_permissions(request, project)

        project.is_archived = not project.is_archived
        project.save()

        return Response(
            {
                "message": "Project archived" if project.is_archived else "Project unarchived",
                "project": ProjectArchiveSerializer(project).data,
            },
            status=status.HTTP_200_OK,
        )


class ArchivedProjectsListView(generics.ListAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(
            is_archived=True
        ).filter(
            models.Q(owner=user) | models.Q(shared_access__user=user)
        ).distinct()
