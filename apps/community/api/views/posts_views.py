from rest_framework import generics, viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Count
from community.models import Post, Comment, PostLike
from community.api import (
PostReadSerializer, 
    PostWriteSerializer, 
    CommentReadSerializer, 
    CommentWriteSerializer
)

from community.models import Community, CommunityMember


# ---------------------------------------------------------
# 1. POST VIEWS
# ---------------------------------------------------------

class CommunityPostListCreateView(generics.ListCreateAPIView):
    """
    ENDPOINT: /api/communities/<community_id>/posts/
    USAGE: 
    - GET: Lists posts for a SPECIFIC community (The 'Social' View)
    - POST: Create a new post in that community
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        community_id = self.kwargs['community_id']
        return Post.objects.filter(community_id=community_id)\
            .select_related('author', 'community')\
            .prefetch_related('attachments', 'likes')\
            .order_by('-is_pinned', '-created_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PostWriteSerializer
        return PostReadSerializer

    def perform_create(self, serializer):
        community = get_object_or_404(Community, id=self.kwargs['community_id'])
        # Check if user is a member here before letting them post
        if not CommunityMember.objects.filter(community=community, user=self.request.user).exists():
             raise permissions.PermissionDenied("You must be a member to post.")
             
        serializer.save(author=self.request.user, community=community)


class HomeActivityFeedView(generics.ListAPIView):
    """
    ENDPOINT: /api/feed/home/
    USAGE: Lists posts from ALL communities the user belongs to.
    This is for the 'Home Dashboard' widget.
    """
    serializer_class = PostReadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # 1. Get IDs of communities I am a member of
        my_community_ids = CommunityMember.objects.filter(
            user=self.request.user
        ).values_list('community_id', flat=True)

        # 2. Filter posts only from those communities
        return Post.objects.filter(community__id__in=my_community_ids)\
            .select_related('author', 'community')\
            .prefetch_related('attachments')\
            .order_by('-created_at')


class PostDetailView(generics.RetrieveDestroyAPIView):
    """
    ENDPOINT: /api/posts/<post_id>/
    USAGE: Get single post or Delete post
    """
    queryset = Post.objects.all()
    serializer_class = PostReadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_destroy(self, instance):
        if instance.author != self.request.user:
             raise permissions.PermissionDenied("You can only delete your own posts.")
        instance.delete()


# ---------------------------------------------------------
# 2. INTERACTION VIEWS (Likes & Comments)
# ---------------------------------------------------------

class ToggleLikeView(APIView):
    """
    ENDPOINT: /api/posts/<post_id>/like/
    USAGE: POST to toggle like/unlike
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        like, created = PostLike.objects.get_or_create(user=request.user, post=post)

        if not created:
            like.delete()
            return Response({"status": "unliked", "count": post.likes.count()})
        
        return Response({"status": "liked", "count": post.likes.count()})


class PostCommentListCreateView(generics.ListCreateAPIView):
    """
    ENDPOINT: /api/posts/<post_id>/comments/
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Comment.objects.filter(post_id=self.kwargs['post_id']).order_by('created_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CommentWriteSerializer
        return CommentReadSerializer

    def perform_create(self, serializer):
        post = get_object_or_404(Post, id=self.kwargs['post_id'])
        serializer.save(author=self.request.user, post=post)