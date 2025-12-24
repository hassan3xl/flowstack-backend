from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ..views.community_views import (
    CommunityViewSet,
    CommunityCategoryListView,
    ReceivedInvitationListView,
    CreateInvitationView,
    AcceptInvitationView,
    RejectInvitationView,
    CommunityIconUploadView,
    CommunityMemberRoleView,
    InvitePreviewView,
    JoinCommunityByInviteView
)

# Initialize Router for the ViewSet
router = DefaultRouter()
router.register(r'communities', CommunityViewSet, basename='community')

urlpatterns = [
   

    # --- Categories ---
    path('communities/categories/', CommunityCategoryListView.as_view(), name='category-list'),

    # --- Community Management Utility ---
    path('communities/<uuid:community_id>/upload-icon/', CommunityIconUploadView.as_view(), name='upload-icon'),
    path('communities/<uuid:community_id>/members/<uuid:user_id>/role/', CommunityMemberRoleView.as_view(), name='update-member-role'),

    # --- Invitation Flow (Creating & Receiving) ---
    # 1. User sees invites sent TO them
    path('invitations/received/', ReceivedInvitationListView.as_view(), name='received-invitations'),
    
    # 2. Creator sends an invite (context: inside a community)
    path('communities/<uuid:community_id>/invite/', CreateInvitationView.as_view(), name='create-invitation'),

    # 3. User responds to a direct invite
    path('invitations/<uuid:invite_id>/accept/', AcceptInvitationView.as_view(), name='accept-invitation'),
    path('invitations/<uuid:invite_id>/reject/', RejectInvitationView.as_view(), name='reject-invitation'),

    # --- Public Invite Link Flow (Discord Style) ---
    # 4. Public clicks a link (e.g., example.com/invite/AbCdEfG) -> API checks validity
    path('invites/<str:invite_code>/preview/', InvitePreviewView.as_view(), name='invite-preview'),
    
    # 5. Public confirms "Join Server" button
    path('invites/join/', JoinCommunityByInviteView.as_view(), name='join-by-invite'),
]

# Include the router's URLs
urlpatterns += [
     # --- Router URLs (CRUD for Communities) ---
    # This automatically generates:
    # GET /communities/ -> List & Create
    # GET /communities/{id}/ -> Retrieve, Update, Delete
    # GET /communities/public_communities/ -> Custom action
    # GET /communities/{id}/members/ -> Custom action
    path('', include(router.urls)),
]