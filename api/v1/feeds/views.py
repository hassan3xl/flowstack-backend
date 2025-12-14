from .serializers import FeedReadSerializer,  FeedWriteSerializer, FeedCommentReadSerializer, FeedCommentWriteSerializer
from feed_manager.models import Feed, FeedComment, FeedLike
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from server_manager.models import ServerMember, Server
from django.core.exceptions import PermissionDenied



# feed_manager/utils.py
from server_manager.models import ServerMember
from django.core.exceptions import PermissionDenied

def assert_server_membership(user, server):
    if not ServerMember.objects.filter(server=server, user=user).exists():
        raise PermissionDenied("You are not a member of this server.")


class FeedListView(generics.ListAPIView):
    serializer_class = FeedReadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Feed.objects
            .filter(server__members__user=self.request.user)
            .select_related("author", "server")
            .prefetch_related("feed_comments", "feed_likes")
        )



class ServerFeedListView(generics.ListAPIView):
    serializer_class = FeedReadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        server_id = self.kwargs["server_id"]
        return (
            Feed.objects
            .filter(
                server_id=server_id,
                server__members__user=self.request.user
            )
            .select_related("author", "server")
            .prefetch_related("feed_comments", "feed_likes")
        )



class ServerFeedCreateView(generics.CreateAPIView):
    serializer_class = FeedWriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        server = get_object_or_404(Server, id=self.kwargs["server_id"])
        assert_server_membership(self.request.user, server)

        serializer.save(
            author=self.request.user,
            server=server
        )


class FeedDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return FeedWriteSerializer
        return FeedReadSerializer

    def get_queryset(self):
        return Feed.objects.filter(
            server__members__user=self.request.user
        )

    def perform_update(self, serializer):
        feed = self.get_object()
        if feed.author != self.request.user:
            raise PermissionDenied("You can only edit your own feeds.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            raise PermissionDenied("You can only delete your own feeds.")
        instance.delete()


class FeedCommentCreateView(generics.CreateAPIView):
    serializer_class = FeedCommentWriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        feed = get_object_or_404(Feed, id=self.kwargs["feed_id"])
        assert_server_membership(self.request.user, feed.server)

        serializer.save(
            feed=feed,
            author=self.request.user
        )


class FeedCommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return FeedCommentWriteSerializer
        return FeedCommentReadSerializer

    def get_queryset(self):
        return FeedComment.objects.filter(
            feed__server__members__user=self.request.user
        )

    def perform_update(self, serializer):
        comment = self.get_object()
        if comment.author != self.request.user:
            raise PermissionDenied("You can only edit your own comments.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            raise PermissionDenied("You can only delete your own comments.")
        instance.delete()
