from django.urls import path
from .views import FeedListView, FeedDetailView, ServerFeedListView

urlpatterns = [
    path('', FeedListView.as_view(), name='feed-list'),
    path("<uuid:server_id>/feeds/", ServerFeedListView.as_view(), name="server-feed-list"),
]