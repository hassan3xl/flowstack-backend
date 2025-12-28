from rest_framework import permissions
from django.shortcuts import get_object_or_404
from ..models import WorkspaceMember, ProjectMember, Workspace

class IsWorkspaceMemberOrAdmin(permissions.BasePermission):
    """
    Handles permissions for Workspace interactions.
    - READ (GET): Must be a member of the workspace.
    - WRITE (PUT, PATCH, DELETE): Must be 'admin' or 'owner' of the workspace.
    """

    def has_permission(self, request, view):
        # 1. Global Authentication Check
        if not request.user.is_authenticated:
            return False
            
        # 2. If this is a list view or specific view not using get_object() immediately,
        # we might check 'workspace_id' from the URL if available.
        workspace_id = view.kwargs.get('workspace_id') or view.kwargs.get('pk')
        
        # If we can't find an ID in the URL, we let the view handle logic 
        # (e.g., creating a new workspace doesn't need a specific ID check here)
        if not workspace_id:
            return True

        # Check if user is a member of this workspace
        return WorkspaceMember.objects.filter(
            workspace_id=workspace_id, 
            user=request.user
        ).exists()

    def has_object_permission(self, request, view, obj):
        # This is called when view.get_object() runs.
        # 'obj' is the actual Workspace instance.

        # 1. Verify Membership again (Safeguard)
        membership = WorkspaceMember.objects.filter(
            workspace=obj, 
            user=request.user
        ).first()

        if not membership:
            return False

        # 2. Safe Methods (GET, HEAD, OPTIONS) -> Allow any member
        if request.method in permissions.SAFE_METHODS:
            return True

        # 3. Unsafe Methods (PUT, DELETE) -> Must be Admin or Owner
        return membership.role in ['admin', 'owner']


class IsProjectCollaboratorOrWorkspaceAdmin(permissions.BasePermission):
    """
    Handles permissions for Project interactions nested inside a Workspace.
    - Prerequisite: Must be a Workspace Member.
    - READ (GET): Must be a Project Member OR Workspace Admin/Owner.
    - WRITE (PUT, DELETE PROJECT): Must be Workspace Admin/Owner (as requested).
    """

    def has_permission(self, request, view):
        # 1. Check Workspace Membership "Gatekeeper"
        if not request.user.is_authenticated:
            return False

        workspace_id = view.kwargs.get('workspace_id')
        
        if workspace_id:
            is_workspace_member = WorkspaceMember.objects.filter(
                workspace_id=workspace_id, 
                user=request.user
            ).exists()
            
            if not is_workspace_member:
                return False
                
        return True

    def has_object_permission(self, request, view, obj):
        # 'obj' here is the PROJECT instance
        
        # Fetch the user's role in the PARENT workspace
        workspace_membership = WorkspaceMember.objects.filter(
            workspace=obj.workspace,
            user=request.user
        ).first()

        if not workspace_membership:
            return False

        # 1. ADMIN/OWNER OVERRIDE
        # If user is Workspace Admin/Owner, they can do ANYTHING to the project
        if workspace_membership.role in ['admin', 'owner']:
            return True

        # 2. WRITE Access (Update/Delete Project)
        # As per your request: only Admins/Owners can update/delete projects.
        # Regular members are denied here.
        if request.method not in permissions.SAFE_METHODS:
            return False

        # 3. READ Access (Viewing the project)
        # Check if they are explicitly added to the project
        is_project_collaborator = ProjectMember.objects.filter(
            project=obj,
            user=request.user
        ).exists()

        # Allow access if they are a collaborator OR if the project is visible to the whole workspace
        if is_project_collaborator:
            return True
            
        if obj.visibility == 'public':
            return True

        return False

class IsTaskCollaboratorOrProjectAdmin(permissions.BasePermission):
    """
    Handles permissions for Task interactions nested inside a Project.
    
    Hierarchy:
    1. Workspace Admin/Owner: Full Access (Super override).
    2. Project Member:
       - READ (GET): Allowed if user is a member of the project.
       - WRITE (PUT, PATCH, DELETE): Allowed ONLY if project membership has 'write' permission.
    """

    def has_permission(self, request, view):
        # 1. Global Auth Check
        if not request.user.is_authenticated:
            return False
            
        # (Optional) fail-fast logic if project_id is in URL
        # We rely on has_object_permission for the specific logic
        return True

    def has_object_permission(self, request, view, obj):
        # 'obj' is the TASK instance
        project = obj.project
        workspace = project.workspace

        # 1. Fetch Workspace Membership (The absolute prerequisite)
        workspace_member = WorkspaceMember.objects.filter(
            workspace=workspace,
            user=request.user
        ).first()

        if not workspace_member:
            return False

        # 2. ADMIN/OWNER OVERRIDE (Workspace Level)
        # If user is Workspace Admin/Owner, they have full control over tasks.
        if workspace_member.role in ['admin', 'owner']:
            return True

        # 3. Check Project Membership
        # User must be explicitly added to the project to interact with tasks
        project_member = ProjectMember.objects.filter(
            project=project,
            user=request.user
        ).first()

        if not project_member:
            return False

        # 4. READ Access (Safe Methods: GET, HEAD, OPTIONS)
        # If they are a project member (any role), they can view the task.
        if request.method in permissions.SAFE_METHODS:
            return True

        # 5. WRITE Access (Unsafe Methods: PUT, PATCH, DELETE)
        # Check if the project member specifically has 'write' permission.
        # NOTE: Adjust 'permission' to whatever field name you use (e.g., 'role', 'access_level')
        return project_member.permission == 'write'