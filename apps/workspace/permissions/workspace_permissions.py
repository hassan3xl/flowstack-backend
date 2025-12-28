from rest_framework import permissions
from ..models import WorkspaceMember, Workspace



def get_workspace_from_obj(obj):
    """
    Safely resolve the Workspace instance from any related object.

    Supported:
    - Workspace
    - WorkspaceChannel
    - ActivityLog
    - WorkspaceInvitation
    - Any model with a `workspace` FK
    """
    if hasattr(obj, "workspace"):
        return obj.workspace
    return obj

class IsWorkspaceMember(permissions.BasePermission):
    """
    User must be a member of the workspace (or owner).
    """

    def has_permission(self, request, view):
        # Required for list, create, and custom actions
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        workspace = obj if isinstance(obj, Workspace) else obj.workspace

        if workspace.owner == request.user:
            return True

        return WorkspaceMember.objects.filter(
            workspace=workspace,
            user=request.user
        ).exists()


class IsWorkspaceAdmin(permissions.BasePermission):
    """
    Allows access only to Workspace Admins and Owners.

    Use cases:
    - Update workspace
    - Manage members
    - Create/update/delete channels
    - Send invitations
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        workspace = get_workspace_from_obj(obj)

        # Workspace owner always has admin rights
        if workspace.owner == request.user:
            return True

        return WorkspaceMember.objects.filter(
            workspace=workspace,
            user=request.user,
            role="admin"
        ).exists()


class IsWorkspaceOwner(permissions.BasePermission):
    """
    Strict permission.

    Only the actual Workspace owner may perform the action.
    Typical usage:
    - Delete workspace
    - Transfer ownership
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        workspace = get_workspace_from_obj(obj)
        return workspace.owner == request.user
