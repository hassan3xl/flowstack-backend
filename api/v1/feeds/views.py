from .serializers import FeedSerializer
from feed_manager.models import Feed, FeedComment, FeedLike
from rest_framework import generics, permissions

class FeedListView(generics.ListAPIView):
    serializer_class = FeedSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Fetch ALL feeds from ALL servers the user belongs to
        return Feed.objects.filter(
            server__members__user=user
        ).select_related("author", "server")


class ServerFeedListView(generics.ListAPIView):
    serializer_class = FeedSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        server_id = self.kwargs.get("server_id")
        user = self.request.user

        # Return feeds ONLY from that server AND only if user is a member
        return Feed.objects.filter(
            server_id=server_id,
            server__members__user=user
        ).select_related("author", "server")



class FeedDetailView(generics.RetrieveAPIView):
    queryset = Feed.objects.all()
    serializer_class = FeedSerializer
    permission_classes = [permissions.IsAuthenticated]
