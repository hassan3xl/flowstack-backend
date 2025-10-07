# permissions.py
from rest_framework import permissions
from .models import SharedListAccess


class IsOwnerOrSharedReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            # Check if user is owner or has shared access
            if hasattr(obj, "owner"):
                return (
                    obj.owner == request.user
                    or obj.shared_access.filter(user=request.user).exists()
                )
            elif hasattr(obj, "todo_list"):
                return (
                    obj.todo_list.owner == request.user
                    or obj.todo_list.shared_access.filter(user=request.user).exists()
                )
        # For write operations, only owner can modify
        if hasattr(obj, "owner"):
            return obj.owner == request.user
        return False


class IsOwnerOrSharedWrite(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, "todo_list"):
            todo_list = obj.todo_list
            if todo_list.owner == request.user:
                return True

            # Check shared access level
            shared_access = SharedListAccess.objects.filter(
                todo_list=todo_list, user=request.user
            ).first()

            if shared_access:
                if request.method in permissions.SAFE_METHODS:
                    return True
                elif request.method in ["PUT", "PATCH", "POST"]:
                    return shared_access.access_level in ["edit", "manage"]
                elif request.method == "DELETE":
                    return shared_access.access_level == "manage"

        return False
