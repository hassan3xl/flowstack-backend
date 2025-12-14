from django.urls import path
from .views import FeedListView, FeedDetailView, ServerFeedListView, ServerFeedCreateView

urlpatterns = [
    path('', FeedListView.as_view(), name='feed-list'),
    path("server/<uuid:server_id>/", ServerFeedListView.as_view(), name="server-feed-list"),
    path("server/<uuid:server_id>/create/", ServerFeedCreateView.as_view(), name="server-feed-list"),

]