# serializers.py
from rest_framework import serializers
from users.models import User, Profile
from django.utils import timezone
import uuid


class AccountUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', ]
    

class AccountProfileSerializer(serializers.ModelSerializer):
    user = AccountUserSerializer(read_only=True)
    avatar = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ["id", "avatar", "first_name", "last_name", "full_name", "username", "bio", "phone_number", "user", ]
        read_only_fields = ('user', 'created_at', 'updated_at')
    
    def get_avatar(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

class AccountProfileAvatarSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(required=True)
    
    class Meta:
        model = Profile
        fields = ["avatar"]
    
    def update(self, instance, validated_data):
        # Handle avatar update
        instance.avatar = validated_data.get('avatar', instance.avatar)
        instance.save()
        return instance