from rest_framework import serializers
from community.models import Post, PostAttachment, Comment, PostLike
from community.models import Community
from users.api.serializers.user_serializers import UserSerializer

# --- Attachment Serializer ---
class PostAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostAttachment
        fields = ["id", "file", "file_type"]

# --- Comment Serializers ---
class CommentReadSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "author", "content", "created_at", "updated_at"]

class CommentWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["content"]

# --- Post Serializers ---
class PostReadSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    community_name = serializers.CharField(source="community.name", read_only=True)
    community_id = serializers.UUIDField(source="community.id", read_only=True)
    
    # Nested Relations
    attachments = PostAttachmentSerializer(many=True, read_only=True)
    
    # We usually don't load ALL comments in the feed, just the count
    comment_count = serializers.IntegerField(source="comments.count", read_only=True)
    like_count = serializers.IntegerField(source="likes.count", read_only=True)
    
    # Check if current user liked it (Requires 'context' passed from view)
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id",
            "author",
            "community_name",
            "community_id",
            "content",
            "attachments",
            "is_pinned",
            "created_at",
            "updated_at",
            "comment_count",
            "like_count",
            "is_liked",
        ]

    def get_is_liked(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return obj.likes.filter(user=user).exists()
        return False


class PostWriteSerializer(serializers.ModelSerializer):
    # We accept a list of files for upload
    files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Post
        fields = ["content", "files"]

    def create(self, validated_data):
        files_data = validated_data.pop('files', [])
        post = Post.objects.create(**validated_data)
        
        # Create Attachment objects for each uploaded file
        for file in files_data:
            # Simple logic to guess type (expand as needed)
            file_type = 'image' if 'image' in file.content_type else 'file'
            PostAttachment.objects.create(post=post, file=file, file_type=file_type)
            
        return post