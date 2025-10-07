from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    CustomUser,
    UserProfile,
    Project,
    ProjectItem,
    SharedListAccess,
    UserSettings,
)

class CustomUserAdmin(BaseUserAdmin):
    model = CustomUser
    list_display = ("email", "is_staff", "is_active", "created_at")
    list_filter = ("is_staff", "is_active")
    search_fields = ("email",)
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "is_staff", "is_active"),
            },
        ),
    )
    


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "first_name", "last_name", "phone_number")
    search_fields = ("user__email", "first_name", "last_name", "phone_number")


class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "visibility", "is_archived", "created_at")
    list_filter = ("visibility", "is_archived")
    search_fields = ("title", "owner__email")


class ProjectItemAdmin(admin.ModelAdmin):
    list_display = ("title", "priority", "status", "due_date", "completed_at")
    list_filter = ("priority", "status",)
    search_fields = ("title", "projects__title")


class SharedListAccessAdmin(admin.ModelAdmin):
    list_display = ("user", "access_level", "shared_by", "created_at")
    list_filter = ("access_level",)
    search_fields = ("projects__title", "user__email", "shared_by__email")


class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ("user", "language", "items_per_page", "enable_email_notifications")
    list_filter = ("language", "enable_email_notifications")
    search_fields = ("user__email",)


# Register all models
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(ProjectItem, ProjectItemAdmin)
admin.site.register(SharedListAccess, SharedListAccessAdmin)
admin.site.register(UserSettings, UserSettingsAdmin)
