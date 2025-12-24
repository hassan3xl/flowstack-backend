from django.db import models
from community.models import Community
import uuid
from users.models import User

# Renamed from 'Feed' to 'Post' to sound less like social media
class Post(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    content = models.TextField(help_text="The main text content of the post")
    
    # Simple pinned logic for "Announcements" in a workspace context
    is_pinned = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at'] # Pinned posts first, then new ones
        verbose_name = "Community Post"
        verbose_name_plural = "Community Posts"

    def __str__(self):
        return f"{self.author.profile.username} in {self.community.name}"


# New Model: Handles Images and Files separately
class PostAttachment(models.Model):
    MEDIA_TYPES = (
        ('image', 'Image'),
        ('video', 'Video'),
        ('file', 'File'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(upload_to='post_attachments/')
    file_type = models.CharField(max_length=10, choices=MEDIA_TYPES, default='image')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for {self.post.id}"


class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='post_comments'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at'] # Oldest first usually makes sense for reading flow

    def __str__(self):
        return f"Comment by {self.author.profile.username}"


class PostLike(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='likes'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='liked_posts'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user') # Prevent double liking

    def __str__(self):
        return f"{self.user.profile.username} likes {self.post.id}"