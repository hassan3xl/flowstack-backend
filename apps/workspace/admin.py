from django.contrib import admin
from .models import Workspace, WorkspaceChannel, WorkspaceMember

admin.site.register(Workspace)
admin.site.register(WorkspaceChannel)
admin.site.register(WorkspaceMember)


# Register your models here.
