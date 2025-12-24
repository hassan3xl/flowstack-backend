from django.urls import path
from ..views.posts_views import (
    PostDetailView,
     HomeActivityFeedView,
    CommunityPostListCreateView,
    PostDetailView,
    ToggleLikeView,
    PostCommentListCreateView
)

urlpatterns = [
    # --- The "Workspace First" Home Feed ---
    # Shows mixed posts from all communities the user is part of (for the Dashboard)
    path('home/', HomeActivityFeedView.as_view(), name='home-activity-feed'),

    # --- Community Specific Feed ---
    # Shows posts only for one specific community (The "Social" view)
    # GET: List posts, POST: Create new post
    path('communities/<uuid:community_id>/posts/', CommunityPostListCreateView.as_view(), name='community-posts'),

    # --- Single Post Operations ---
    # GET: Retrieve post details, DELETE: Delete post
    path('posts/<uuid:pk>/', PostDetailView.as_view(), name='post-detail'),

    # --- Interactions (Likes & Comments) ---
    path('posts/<uuid:post_id>/like/', ToggleLikeView.as_view(), name='post-like'),
    path('posts/<uuid:post_id>/comments/', PostCommentListCreateView.as_view(), name='post-comments'),
]