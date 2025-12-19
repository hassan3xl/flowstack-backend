# feed_manager/serializers/comment.py
from rest_framework import serializers
from feed_manager.models import FeedComment, FeedLike, Feed
from ..account.serializers import UserSerializer


class FeedCommentReadSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = FeedComment
        fields = [
            "id",
            "author",
            "content",
            "created_at",
            "updated_at",
        ]


class FeedCommentWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedComment
        fields = ["content"]


class FeedLikeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = FeedLike
        fields = ["id", "author", "created_at"]



class FeedReadSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    server = serializers.CharField(source="server.name", read_only=True)
    server_id = serializers.UUIDField(source="server.id", read_only=True)

    comments = FeedCommentReadSerializer(
        source="feed_comments",
        many=True,
        read_only=True
    )
    likes = FeedLikeSerializer(
        source="feed_likes",
        many=True,
        read_only=True
    )

    comment_count = serializers.IntegerField(
        source="feed_comments.count",
        read_only=True
    )
    like_count = serializers.IntegerField(
        source="feed_likes.count",
        read_only=True
    )

    class Meta:
        model = Feed
        fields = [
            "id",
            "author",
            "server",
            "server_id",
            "content",
            "created_at",
            "updated_at",
            "comments",
            "likes",
            "comment_count",
            "like_count",
        ]


class FeedWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feed
        fields = ["content"]


