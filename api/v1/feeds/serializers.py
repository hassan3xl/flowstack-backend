# serializers.py
from rest_framework import serializers
from ..account.serializers import UserSerializer
from django.utils import timezone
import uuid
from user_manager.models import UserProfile, CustomUser
from feed_manager.models import Feed, FeedComment, FeedLike

class CommentSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='author.profile.username', read_only=True)
    class Meta:
        model = FeedComment
        fields = ['id', 'author', 'content', 'created_at', 'updated_at']
        read_only_fields = ("id", "created_at", "updated_at")

class LikeSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='author.profile.username', read_only=True)
    class Meta:
        model = FeedLike
        fields = ['id', 'author', 'created_at', 'updated_at']
        read_only_fields = ("id", "created_at", "updated_at")

class FeedSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='author.profile.username', read_only=True)
    server = serializers.CharField(source='server.name', read_only=True)
    server_id = serializers.UUIDField(source='server.id', read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    likes = LikeSerializer(many=True, read_only=True)
    comment_count = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()

    class Meta:
        model = Feed
        fields = ['id', 'author', 'server', 'server_id', 'content', 'created_at', 'updated_at', 'comments', 'likes', 'comment_count', 'like_count']
        read_only_fields = ("id", "created_at", "updated_at")
    
    def get_comment_count(self, obj):
        return obj.feed_comments.count()
    
    def get_like_count(self, obj):
        return obj.feed_likes.count()

class FeedWriteSerializer(serializers.ModelSerializer):
    server = serializers.UUIDField(required=True)
    class Meta:
        model = Feed
        fields = ['id', 'content', 'server']
        read_only_fields = ("id", "created_at", "updated_at")