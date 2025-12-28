# permissions.py
from rest_framework import permissions
from ..models import WorkspaceMember, ProjectMember

class HasProjectAccess(permissions.BasePermission):
    def has_permission(self, request, view):
        # 1. Get the workspace_id from the URL
        workspace_id = view.kwargs.get('workspace_id') 

        # 2. CHECK WORKSPACE LEVEL (The "God Mode" check)
        # If user is Workspace Owner/Admin, they generally can do anything.
        is_workspace_admin = WorkspaceMember.objects.filter(
            user=request.user, 
            workspace_id=workspace_id, 
            role__in=['owner', 'admin']
        ).exists()

        if is_workspace_admin:
            return True

        # 3. CHECK PROJECT LEVEL
        # If we are acting on a list of projects, we might return True here 
        # and let 'get_queryset' filter the list later. 
        # But if we are accessing a specific project object, has_object_permission handles it.
        return True

    def has_object_permission(self, request, view, obj):
        # 'obj' here is the Project instance
        
        # 1. Re-check Workspace Admin (because has_object_permission runs after has_permission)
        workspace_role = WorkspaceMember.objects.filter(
            user=request.user, 
            workspace=obj.workspace
        ).values_list('role', flat=True).first()

        if workspace_role in ['owner', 'admin']:
            return True

        # 2. Check Project Membership
        try:
            project_member = ProjectMember.objects.get(
                user=request.user, 
                project=obj
            )
        except ProjectMember.DoesNotExist:
            return False

        # 3. Granular Action Check
        # Define what roles can do what methods
        if request.method in permissions.SAFE_METHODS: # GET, HEAD, OPTIONS
            return True # Viewers and Editors can both read
            
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            # Only Editors can write
            return project_member.role == 'write'

        return False