from rest_framework import viewsets, status, generics, permissions
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import NotFound

from workspace.models import (
    Workspace,
    WorkspaceMember,
    WorkspaceInvitation,
    Project, Task, ProjectMember,
    WorkspaceChannel
)
from workspace.api import (
    WorkspaceSerializer,
    CreateWorkspaceSerializer,
    WorkspaceMemberSerializer,
    CreateWorkspaceInvitationSerializer,
    UploadWorkspaceLogoSerializer,
    WorkspaceDashboardSerializer
)

from django.utils import timezone

class WorkspaceDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, workspace_id):
        user = request.user

        # Ensure user is a member of workspace
        workspace = get_object_or_404(
            Workspace,
            id=workspace_id,
            members__user=user
        )

        projects_qs = Project.objects.filter(workspace=workspace)
        tasks_qs = Task.objects.filter(project__workspace=workspace)

        data = {
            "projects": projects_qs.count(),
            "tasks": tasks_qs.count(),
            "completed_tasks": tasks_qs.filter(
                status=Task.StatusChoices.COMPLETED
            ).count(),
            "members": WorkspaceMember.objects.filter(workspace=workspace).count(),
        }

        serializer = WorkspaceDashboardSerializer(data)
        return Response(serializer.data)
    
class WorkspaceViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Workspace.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return CreateWorkspaceSerializer
        return WorkspaceSerializer

    def get_queryset(self):
        user = self.request.user
        return Workspace.objects.filter(
            Q(owner=user) |
            Q(members__user=user)
        ).distinct()

    def perform_create(self, serializer):
        workspace = serializer.save(owner=self.request.user)

        # Ensure owner is also a member
        WorkspaceMember.objects.create(
            workspace=workspace,
            user=self.request.user,
            role="owner",
        )

        return workspace


    @action(detail=True, methods=["get"], url_path="members")
    def members(self, request, pk=None):
        workspace = self.get_object()

        members = WorkspaceMember.objects.filter(
            workspace=workspace
        ).select_related("user")

        serializer = WorkspaceMemberSerializer(members, many=True)
        return Response(serializer.data)


class CreateWorkspaceInvitationView(generics.CreateAPIView):
    serializer_class = CreateWorkspaceInvitationSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        workspace_id = self.kwargs["workspace_id"]
        workspace = get_object_or_404(Workspace, id=workspace_id)

        # Only owner/admin can invite
        try:
            member = WorkspaceMember.objects.get(
                workspace=workspace,
                user=self.request.user
            )
        except WorkspaceMember.DoesNotExist:
            return Response(
                {"error": "You are not a member of this workspace."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if member.role not in ["owner", "admin"]:
            return Response(
                {"error": "Only admins can invite users."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer.save(workspace=workspace)


class AcceptWorkspaceInvitationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, invite_id):
        user = request.user

        invite = get_object_or_404(
            WorkspaceInvitation,
            id=invite_id,
            invited_user=user,
        )

        # Expiration check
        if invite.expires_at and invite.expires_at < timezone.now():
            return Response(
                {"error": "Invite has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Prevent duplicate membership
        if WorkspaceMember.objects.filter(
            workspace=invite.workspace,
            user=user
        ).exists():
            return Response(
                {"error": "You are already a member of this workspace."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        WorkspaceMember.objects.create(
            workspace=invite.workspace,
            user=user,
            role=invite.role,
        )

        invite.delete()  # invitations are one-time

        return Response(
            {"message": "You have joined the workspace."},
            status=status.HTTP_200_OK,
        )


class RejectWorkspaceInvitationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, invite_id):
        invite = get_object_or_404(
            WorkspaceInvitation,
            id=invite_id,
            invited_user=request.user,
        )

        invite.delete()

        return Response(
            {"message": "Invitation rejected."},
            status=status.HTTP_200_OK,
        )


class WorkspaceImageUploadView(generics.UpdateAPIView):
    serializer_class = UploadWorkspaceLogoSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self):
        workspace_id = self.kwargs["workspace_id"]
        workspace = get_object_or_404(Workspace, id=workspace_id)

        # Only owner/admin
        member = get_object_or_404(
            WorkspaceMember,
            workspace=workspace,
            user=self.request.user,
        )

        if member.role not in ["owner", "admin"]:
            raise permissions.PermissionDenied(
                "You do not have permission to update this workspace."
            )

        return workspace


class WorkspaceMemberRoleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, workspace_id, user_id):
        workspace = get_object_or_404(Workspace, id=workspace_id)

        requester = get_object_or_404(
            WorkspaceMember,
            workspace=workspace,
            user=request.user,
        )

        if requester.role not in ["owner", "admin"]:
            return Response(
                {"error": "Only admins can update roles."},
                status=status.HTTP_403_FORBIDDEN,
            )

        member = get_object_or_404(
            WorkspaceMember,
            workspace=workspace,
            user__id=user_id,
        )

        if member.user == request.user:
            return Response(
                {"error": "You cannot change your own role."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        role = request.data.get("role")
        if role not in dict(WorkspaceMember.ROLE_CHOICES):
            return Response(
                {"error": "Invalid role."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        member.role = role
        member.save(update_fields=["role"])

        return Response(
            {
                "message": "Role updated successfully.",
                "user": member.user.id,
                "role": member.role,
            },
            status=status.HTTP_200_OK,
        )


