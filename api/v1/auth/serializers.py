from rest_framework import serializers
from django.contrib.auth import get_user_model
from user_manager.models import UserProfile


User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, style={'input_type': 'password'})
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['email', 'password1', 'password2', 'first_name', 'last_name']

    def validate(self, data):
        if data['password1'] != data['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        password = validated_data.pop('password1')
        validated_data.pop('password2')

        # Pop optional fields safely
        first_name = validated_data.pop('first_name', '').strip()
        last_name = validated_data.pop('last_name', '').strip()

        # Create the user
        user = User.objects.create_user(password=password, **validated_data)

        # Always create profile, even if no names provided
        UserProfile.objects.create(
            user=user,
            first_name=first_name or "",
            last_name=last_name or ""
        )

        return user



class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
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
    # profile = ProfileSerializer(read_only=True)
    fullname = serializers.SerializerMethodField()
    username = serializers.CharField(source='profile.username', read_only=True)

    class Meta:
        model = User
        fields = ("id", "email", "username", "fullname") 

    def get_fullname(self, obj):
        profile = getattr(obj, "profile", None)
        if profile and profile.first_name and profile.last_name:
            return f"{profile.first_name} {profile.last_name}"
        return ""
