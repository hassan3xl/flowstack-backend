import uuid
from django.db import models
from .user import User
from ..utils.generate_username import generate_username


class Profile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile"
    )
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    username = models.CharField(max_length=100, unique=True, blank=True, null=True, default=generate_username)
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(
        upload_to="avatars/", blank=True, null=True
    )
    phone_number = models.CharField(max_length=20, blank=True)
    email_notifications = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        db_table = "user_profiles"
        indexes = [
            # Create an index for phone_number
            models.Index(fields=['phone_number']),
            
            # Composite Index: fast for searching first AND last name together
            models.Index(fields=['first_name', 'last_name']),
        ]

    def __str__(self):
        return f"{self.user.email}'s Profile"

