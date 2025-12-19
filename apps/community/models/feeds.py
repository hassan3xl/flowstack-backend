from django.db import models
from community.models import Community
import uuid
from users.models import User

class Feed(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='feed_posts'   
    )
    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name='community_feeds'  
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.author.profile.username} - {self.created_at}"


class FeedComment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    feed = models.ForeignKey(
        Feed,
        on_delete=models.CASCADE,
        related_name='feed_comments'  
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='feed_comments_authored'  
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.author.profile.username} - {self.feed.content[:50]}..."


class FeedLike(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    feed = models.ForeignKey(
        Feed,
        on_delete=models.CASCADE,
        related_name='feed_likes'   
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='feed_likes_authored'  
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.author.profile.username} - {self.feed.content[:50]}..."
