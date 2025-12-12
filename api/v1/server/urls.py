from django.urls import path, include
from .views import (
    ServerViewSet, 
    CreateServerInvitationView, 
    ReceivedInvitationListView, AcceptInvitationView, RejectInvitationView,
    ServerStatsAndRecentActivitiesView,
)

from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'servers', ServerViewSet, basename='server')

urlpatterns = [
    path('', include(router.urls)),

    # Server stats and recent activities
    path(
        "servers/<uuid:server_id>/stats/",
        ServerStatsAndRecentActivitiesView.as_view(),
        name="server-stats"
    ),

    # Create invitation
    path(
        "servers/<uuid:server_id>/invite/",
        CreateServerInvitationView.as_view(),
        name="create-server-invite"
    ),

    # List invitations sent to the logged-in user
    path(
        "servers/invites/received/",
        ReceivedInvitationListView.as_view(),
        name="received-invites"
    ),

    # Accept invitation
    path(
        "servers/invites/<uuid:invite_id>/accept/",
        AcceptInvitationView.as_view(),
        name="accept-invite"
    ),

    # Reject invitation
    path(
        "servers/invites/<uuid:invite_id>/reject/",
        RejectInvitationView.as_view(),
        name="reject-invite"
    ),
]