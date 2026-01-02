from rest_framework import serializers
from django.contrib.auth import get_user_model
from users.models import Profile
from notifications.notification_services import NotificationService

User = get_user_model()
from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers
from notifications.notification_services import NotificationService

# We inherit from the Library's serializer, not ModelSerializer
class CustomRegisterSerializer(RegisterSerializer):
    username = None




class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = (
            "id",
            "first_name",
            "last_name",
            "username",
            "bio",
            "avatar",
            "phone_number",
            "email_notifications",
        )

class UserSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()
    username = serializers.CharField(source='profile.username', read_only=True)
    avatar = serializers.CharField(source='profile.avatar', read_only=True)

    class Meta:
        model = User
        fields = ("id", "email", "username", "fullname", "avatar") 

    def get_fullname(self, obj):
        profile = getattr(obj, "profile", None)
        if profile and profile.first_name and profile.last_name:
            return f"{profile.first_name} {profile.last_name}"
        return ""
