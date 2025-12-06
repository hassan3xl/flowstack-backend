from django.contrib import admin

# Register your models here.
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    Project,
    ProjectItem,
    Comment,
)



class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "created_at")


class ProjectItemAdmin(admin.ModelAdmin):
    list_display = ("title", "priority", "status", "due_date", "completed_at")
    list_filter = ("priority", "status",)
    search_fields = ("title", "projects__title")


# Register all models
admin.site.register(Project, ProjectAdmin)
admin.site.register(ProjectItem, ProjectItemAdmin)
admin.site.register(Comment)