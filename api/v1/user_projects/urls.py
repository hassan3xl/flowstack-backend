from django.urls import path
from . import views

urlpatterns = [
    # Project Lists
    path("", views.ProjectListCreateView.as_view(), name="project-list"),
    path("<uuid:pk>/", views.ProjectDetailView.as_view(), name="project_item-detail"),
    path("<uuid:pk>/settings/", views.ProjectSettingsView.as_view(), name="project-settings"),
    path("<uuid:project_id>/invite/", views.ProjectInviteView.as_view(), name="project-invite"),
    path("<uuid:pk>/archive/", views.ProjectArchiveToggleView.as_view(), name="project-archive-toggle"),
    path("<uuid:project_id>/users/<uuid:user_id>/", views.ProjectRemoveUserView.as_view(), name="remove-user"),

    # Project Items
    path("<uuid:project_id>/items/", views.ProjectItemCreateView.as_view(), name="ptoject_items"),
    path('<uuid:project_id>/tasks/<uuid:task_id>/start/', views.StartTaskView.as_view(), name='start-task'),
    path(
        "<uuid:project_id>/tasks/<uuid:task_id>/complete/",
        views.CompleteTaskView.as_view(),
        name="complete-task"
    ),
    path("<uuid:item_id>/comments/", views.CommentListCreateView.as_view(), name="projectitem-comments"),

    # Shared Lists
    path("shared-lists/", views.SharedListListCreateView.as_view(), name="sharedlist-list"),
    path("shared-lists/<uuid:pk>/", views.SharedListDetailView.as_view(), name="sharedlist-detail"),

    #archiving
    path("archives/", views.ArchivedProjectsListView.as_view(), name="archived-projects-list"),
]

