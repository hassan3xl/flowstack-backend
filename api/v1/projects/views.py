from rest_framework import viewsets, status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from project_manager.models import Project, ProjectItem
from server_manager.models import Server, ServerMember

from .serializers import (
    ProjectSerializer,
    ProjectWriteSerializer,
    ProjectItemSerializer,
    CommentSerializer,
)


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

