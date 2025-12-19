from workspace.models import Project
from rest_framework.permissions import BasePermission
from django.shortcuts import get_object_or_404
from rest_framework import permissions


class HasProjectAccess(BasePermission):
    def has_object_permission(self, request, view, obj):
        # 'obj' here is likely the Project or the Task (depending on the view)
        
        # If 'obj' is a Task, we need to check the project it belongs to
        if hasattr(obj, 'project'):
            return obj.project.members.filter(user=request.user).exists()
        
        # If 'obj' is the Project itself
        return obj.members.filter(user=request.user).exists()