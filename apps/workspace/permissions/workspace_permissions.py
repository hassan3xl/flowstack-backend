from rest_framework import permissions

from ..models import WorkspaceMember

class IsWorkspaceMember(permissions.BasePermission):
    """
    Allows access to users who are members of the workspace.
    Read-only for normal members, unless specified otherwise.
    """
    def has_object_permission(self, request, view, obj):
        # 1. Superusers always have access
        if request.user.is_superuser:
            return True

        # 2. Check if the object is the Workspace itself
        # If the view is handling a related object (like a Channel), 
        # you might need to check 'obj.workspace' instead.
        workspace = obj
        if hasattr(obj, 'workspace'):
            workspace = obj.workspace

        # 3. Allow if user is the explicit owner defined on the Workspace model
        if workspace.owner == request.user:
            return True

        # 4. Check membership existence
        return WorkspaceMember.objects.filter(
            workspace=workspace, 
            user=request.user
        ).exists()


class IsWorkspaceAdmin(permissions.BasePermission):
    """
    Allows access only to Workspace Admins and Owners.
    Used for updating workspace details (PUT, PATCH).
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        workspace = obj
        if hasattr(obj, 'workspace'):
            workspace = obj.workspace

        # Owner always has admin rights
        if workspace.owner == request.user:
            return True

        # Check for 'admin' or 'owner' role in the membership table
        return WorkspaceMember.objects.filter(
            workspace=workspace,
            user=request.user,
            role__in=['admin', 'owner']
        ).exists()


class IsWorkspaceOwner(permissions.BasePermission):
    """
    Strict permission: Only the actual owner can perform this action.
    Usually applied to DELETE actions.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
            
        workspace = obj
        if hasattr(obj, 'workspace'):
            workspace = obj.workspace

        return workspace.owner == request.user