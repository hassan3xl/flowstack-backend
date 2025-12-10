from project_manager.models import Project, ProjectItem, ProjectCollaborator
from rest_framework.permissions import BasePermission
from django.shortcuts import get_object_or_404
from rest_framework import permissions

class HasProjectAccess(BasePermission):
    def has_object_permission(self, request, view, obj):
        # 'obj' here is likely the Project or the Task (depending on the view)
        
        # If 'obj' is a Task, we need to check the project it belongs to
        if hasattr(obj, 'project'):
            return obj.project.collaborators.filter(user=request.user).exists()
        
        # If 'obj' is the Project itself
        return obj.collaborators.filter(user=request.user).exists()