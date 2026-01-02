from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    User,
    Profile,
    UserSettings,
)

class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ("email", "is_staff", "is_active", "created_at")
    list_filter = ("is_staff", "is_active")
    search_fields = ("email",)
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "created_at",)}),
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
    


class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "first_name", "last_name", "username")
    search_fields = ("user__email", "first_name", "last_name", "username")



class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ("user", "language", "items_per_page", "enable_email_notifications")
    list_filter = ("language", "enable_email_notifications")
    search_fields = ("user__email",)



# Register all models
admin.site.register(User, UserAdmin)
admin.site.register(Profile, ProfileAdmin)

admin.site.register(UserSettings, UserSettingsAdmin)