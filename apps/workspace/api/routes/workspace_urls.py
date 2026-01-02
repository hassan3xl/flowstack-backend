from django.urls import path, include
from rest_framework.routers import DefaultRouter

from ..views.workspace_views import (
    WorkspaceViewSet,
    CreateWorkspaceInvitationView,
    AcceptWorkspaceInvitationView,
    RejectWorkspaceInvitationView,
    WorkspaceImageUploadView,
    WorkspaceMemberRoleView,
    GetWorkspaceInvitationsView,
    RemoveWorkspaceMemberView,
)
from ..views.dashboard_views import (
    WorkspaceDashboardView
)

router = DefaultRouter()
router.register(r'workspaces', WorkspaceViewSet, basename='workspace')


urlpatterns = [
#     # ---------- STATIC / FIXED ROUTES ----------
    path(
        "workspaces/<uuid:workspace_id>/dashboard/",
        WorkspaceDashboardView.as_view(),
        name="workspace-dashboard"
    ),
    path(
        "workspaces/invitations/",
        GetWorkspaceInvitationsView.as_view(),
        name="workspace-invitations"
    ),


]

urlpatterns += [
    # ---------- UUID-CONSTRAINED ROUTES ----------
    path(
        "workspaces/invites/<uuid:invite_id>/accept/",
        AcceptWorkspaceInvitationView.as_view(),
        name="accept-workspace-invite",
    ),

    path(
        "workspaces/invites/<uuid:invite_id>/reject/",
        RejectWorkspaceInvitationView.as_view(),
        name="reject-workspace-invite",
    ),

    path(
        "workspaces/<uuid:workspace_id>/<uuid:user_id>/member-role/",
        WorkspaceMemberRoleView.as_view(),
        name="update-workspace-member-role",
    ),

    path(
        "workspaces/<uuid:workspace_id>/logo/",
        WorkspaceImageUploadView.as_view(),
        name="upload-workspace-icon",
    ),

    path(
        "workspaces/<uuid:workspace_id>/invite/",
        CreateWorkspaceInvitationView.as_view(),
        name="create-workspace-invite",
    ),
    path('workspaces/<uuid:workspace_id>/members/<uuid:member_id>/remove/', 
     RemoveWorkspaceMemberView.as_view(), 
     name='remove-workspace-member'),
]

# urlpatterns += [
#     # ---------- STRING-BASED DYNAMIC ROUTES ----------
#     path(
#         "workspaces/invites/<str:invite_code>/",
#         InvitePreviewView.as_view(),
#         name="workspace-invite-preview",
#     ),
# ]

urlpatterns += [
    # ---------- ROUTER (LAST) ----------
    path("", include(router.urls)),
]
