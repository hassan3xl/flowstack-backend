
from server_manager.models import ServerMember, Server
from rest_framework.permissions import BasePermission
from django.shortcuts import get_object_or_404

def has_server_role(user, server, allowed_roles: list[str]) -> bool:
    return ServerMember.objects.filter(
        server=server,
        user=user,
        role__in=allowed_roles
    ).exists()


def is_server_member(user, server) -> bool:
    return ServerMember.objects.filter(
        server=server,
        user=user
    ).exists()

class IsServerAdminOrMod(BasePermission):
    def has_permission(self, request, view):
        # We assume the URL contains 'server_id'
        server_id = view.kwargs.get("server_id")
        
        # Check if the requesting user has the correct role in this server
        return ServerMember.objects.filter(
            server_id=server_id, 
            user=request.user, 
            role__in=['owner', 'moderator', 'admin'] # Note the __in lookup
        ).exists()
    
class IsServerMember(BasePermission):
    def has_permission(self, request, view):
        server_id = view.kwargs.get("server_id")

        if not server_id:
            return False

        server = get_object_or_404(Server, id=server_id)

        return is_server_member(request.user, server)

class IsServerAdmin(BasePermission):
    def has_permission(self, request, view):
        server_id = view.kwargs.get("server_id")
        if not server_id:
            return False

        server = get_object_or_404(Server, id=server_id)

        return has_server_role(request.user, server, ["owner", "admin"])

class IsServerModerator(BasePermission):
    def has_permission(self, request, view):
        server_id = view.kwargs.get("server_id")
        if not server_id:
            return False

        server = get_object_or_404(Server, id=server_id)

        return has_server_role(
            request.user,
            server,
            ["owner", "admin", "moderator"]
        )

class IsServerOwner(BasePermission):
    def has_permission(self, request, view):
        server_id = view.kwargs.get("server_id")
        if not server_id:
            return False

        server = get_object_or_404(Server, id=server_id)

        return has_server_role(request.user, server, ["owner"])
