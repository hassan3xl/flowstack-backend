from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import uuid

from django.contrib.auth.models import PermissionsMixin
import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from cloudinary.models import CloudinaryField


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.email


class UserProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="profile"
    )
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    username = models.CharField(max_length=30, unique=True, blank=True, null=True)
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

    def __str__(self):
        return f"{self.user.email}'s Profile"

    # generate default username
    def generate_default_username(self):
        return f"{self.first_name.lower()}{self.last_name.lower()}"



class UserSettings(models.Model):
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="settings"
    )
    language = models.CharField(max_length=10, default="en")
    items_per_page = models.IntegerField(default=10)
    default_due_date_days = models.IntegerField(default=7)
    enable_email_notifications = models.BooleanField(default=True)
    enable_push_notifications = models.BooleanField(default=True)
    auto_archive_completed = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_settings"

    def __str__(self):
        return f"{self.user.email}'s Settings"
