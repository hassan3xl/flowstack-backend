from rest_framework import generics, permissions
from django.shortcuts import get_object_or_404
from django.db.models import Q
from core.models import (
    Project,
    ProjectItem,
    SharedListAccess,
)
from .serializers import (
    ProjectSerializer,
    ProjectItemSerializer,
    SharedListAccessSerializer,
    ProjectSettingsSerializer,
    ProjectArchiveSerializer,
)
from core.permissions import HasProjectAccess, IsProjectOwner
from rest_framework.response import Response
from core.models import CustomUser
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from django.db.models import Prefetch


class ProjectListCreateView(generics.ListCreateAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(
            Q(owner=user) | Q(shared_access__user=user),
            is_archived=False
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated, HasProjectAccess]

    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(
            Q(owner=user) |
            Q(shared_access__user=user, shared_access__access_level__in=["read", "write", "manage"])
        ).distinct().prefetch_related(
            Prefetch(
                'project_items',
                queryset=ProjectItem.objects.select_related('started_by__profile')
            ),
        )

class ProjectSettingsView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProjectSettingsSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectOwner]

    def get_queryset(self):
        # Only allow owners to see their own project in settings
        return Project.objects.filter(owner=self.request.user)


class ProjectItemListCreateView(generics.ListCreateAPIView):
    serializer_class = ProjectItemSerializer
    permission_classes = [permissions.IsAuthenticated, HasProjectAccess]

    def get_queryset(self):
        user = self.request.user
        project_id = self.kwargs.get("project_id")
        project = get_object_or_404(Project, id=project_id)

        # Only return items if user is owner or shared
        if not (project.owner == user or project.shared_access.filter(user=user).exists()):
            return ProjectItem.objects.none()

        return ProjectItem.objects.filter(project=project)
    
    def perform_create(self, serializer):
        project_id = self.kwargs.get("project_id")
        project = get_object_or_404(Project, id=project_id)
        serializer.save(project=project)


class StartTaskView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasProjectAccess]

    def post(self, request, project_id, task_id):
        user = request.user
        project = get_object_or_404(Project, id=project_id)

        # Check user access to project
        if not (project.owner == user or project.shared_access.filter(user=user).exists()):
            return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)

        task = get_object_or_404(ProjectItem, id=task_id, project=project)

        # Check if task is free to take
        if task.status != ProjectItem.StatusChoices.PENDING or task.started_by is not None:
            return Response({"detail": "Task is not available to start."}, status=status.HTTP_400_BAD_REQUEST)

        # Assign task to user and change status
        task.started_by = user
        task.status = ProjectItem.StatusChoices.IN_PROGRESS
        task.save()

        serializer = ProjectItemSerializer(task)
        return Response(serializer.data, status=status.HTTP_200_OK)


from rest_framework import status
from django.utils import timezone

class CompleteTaskView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasProjectAccess]

    def post(self, request, project_id, task_id):
        user = request.user
        project = get_object_or_404(Project, id=project_id)

        # Confirm user's access to project
        if not (project.owner == user or project.shared_access.filter(user=user).exists()):
            return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)

        task = get_object_or_404(ProjectItem, id=task_id, project=project)

        # Only tasks in progress can be completed
        if task.status != ProjectItem.StatusChoices.IN_PROGRESS:
            return Response({"detail": "Task cannot be completed in its current state."}, status=status.HTTP_400_BAD_REQUEST)

        task.status = ProjectItem.StatusChoices.COMPLETED
        task.completed_at = timezone.now()
        task.save()

        serializer = ProjectItemSerializer(task)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProjectItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProjectItemSerializer
    permission_classes = [permissions.IsAuthenticated, HasProjectAccess]
    lookup_url_kwarg = "item_id"

    def get_queryset(self):
        user = self.request.user
        return ProjectItem.objects.filter(
            Q(project__owner=user) | Q(project__shared_access__user=user)
        ).distinct()


class ProjectInviteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, project_id):
        """
        Invite an existing user to a project by email.
        The invited user is automatically granted access.
        """
        email = request.data.get("email")
        access_level = request.data.get("access_level", SharedListAccess.AccessLevelChoices.READ)

        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Find the project
        project = get_object_or_404(Project, id=project_id, owner=request.user)

        # Check if user exists
        try:
            invited_user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({"error": "User with this email does not exist"}, status=status.HTTP_404_NOT_FOUND)

        # Prevent inviting self
        if invited_user == request.user:
            return Response({"error": "You cannot invite yourself"}, status=status.HTTP_400_BAD_REQUEST)

        # Create or update access
        shared_access, created = SharedListAccess.objects.get_or_create(
            project=project,
            user=invited_user,
            defaults={
                "access_level": access_level,
                "shared_by": request.user
            }
        )
        if not created:
            # If already exists, just update access level if changed
            shared_access.access_level = access_level
            shared_access.save()

        return Response({
            "message": f"{invited_user.email} has been added to the project",
            "project": project.title,
            "access_level": shared_access.access_level,
        }, status=status.HTTP_201_CREATED)


from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

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



class SharedListListCreateView(generics.ListCreateAPIView):
    serializer_class = SharedListAccessSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SharedListAccess.objects.filter(
            Q(project__owner=self.request.user) | Q(shared_by=self.request.user)
        ).distinct()

    def perform_create(self, serializer):
        instance = serializer.save(shared_by=self.request.user)
       


class SharedListDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SharedListAccessSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SharedListAccess.objects.filter(
            Q(project__owner=self.request.user) | Q(shared_by=self.request.user)
        ).distinct()




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

from django.db import models

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
