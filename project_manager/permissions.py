from rest_framework import permissions
from .models import SharedListAccess, Project


class IsProjectOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, "owner"):
            return obj.owner == request.user
        if hasattr(obj, "project"):
            return obj.project.owner == request.user
        return False


class HasProjectAccess(permissions.BasePermission):
    """
    Unified project permission:
    - Owner: full access
    - READ: can only view
    - WRITE: can view and edit, but not delete
    - MANAGE: full access
    """

    def has_permission(self, request, view):
        """
        Handles non-object level checks (like list or create).
        Restrict POST so only write/manage can create tasks.
        """
        # Allow safe methods globally
        if request.method in permissions.SAFE_METHODS:
            return True

        # Only authenticated users can write
        if not request.user or not request.user.is_authenticated:
            return False

        # Handle project item creation (POST)
        if request.method == "POST":
            project_id = (
                request.data.get("project")
                or view.kwargs.get("project_id")
                or view.kwargs.get("pk")
            )
            if not project_id:
                return False

            try:
                project = Project.objects.get(id=project_id)
            except Project.DoesNotExist:
                return False

            # Owner always allowed
            if project.owner == request.user:
                return True

            shared_access = SharedListAccess.objects.filter(
                project=project, user=request.user
            ).first()

            if shared_access:
                return shared_access.access_level in [
                    SharedListAccess.AccessLevelChoices.WRITE,
                    SharedListAccess.AccessLevelChoices.MANAGE,
                ]

            return False

        # Allow other modifying methods (PUT/PATCH/DELETE) to fall to object-level
        return True

    def has_object_permission(self, request, view, obj):
        # Determine project
        if hasattr(obj, "owner"):
            project = obj
        elif hasattr(obj, "project"):
            project = obj.project
        else:
            return False

        # Owner always full access
        if project.owner == request.user:
            return True

        # Shared access
        shared_access = SharedListAccess.objects.filter(
            project=project, user=request.user
        ).first()

        if not shared_access:
            return False

        if request.method in permissions.SAFE_METHODS:
            return shared_access.access_level in [
                SharedListAccess.AccessLevelChoices.READ,
                SharedListAccess.AccessLevelChoices.WRITE,
                SharedListAccess.AccessLevelChoices.MANAGE,
            ]

        if request.method in ["PUT", "PATCH", "POST"]:
            return shared_access.access_level in [
                SharedListAccess.AccessLevelChoices.WRITE,
                SharedListAccess.AccessLevelChoices.MANAGE,
            ]

        if request.method == "DELETE":
            return shared_access.access_level == SharedListAccess.AccessLevelChoices.MANAGE

        return False
