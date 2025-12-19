from rest_framework_nested import routers
from django.urls import path, include

from ..views.project_views import (

    ProjectViewSet,
    TaskListCreateView,
    TaskRetrieveUpdateView,
    ProjectMemberView,
    StartTaskView,
    CompleteTaskView,
    CommentListCreateView,
)

# ----------------------- ROUTERS -----------------------
router = routers.SimpleRouter()
router.register(
    r'workspaces/(?P<workspace_id>[^/.]+)/projects',
    ProjectViewSet,
    basename='workspace-projects'
)

projects_router = routers.NestedSimpleRouter(
    router,
    r'workspaces/(?P<workspace_id>[^/.]+)/projects',
    lookup='project'
)
# You can register nested viewsets here if needed
# projects_router.register(r'tasks', TaskViewSet, basename='project-tasks')


# ----------------------- URL PATTERNS -----------------------
urlpatterns = [
    path("", include(router.urls)),

    # Tasks
    path(
        "workspaces/<uuid:workspace_id>/projects/<uuid:project_id>/tasks/",
        TaskListCreateView.as_view(),
        name="project-tasks"
    ),
    path(
        "workspaces/<uuid:workspace_id>/projects/<uuid:project_id>/tasks/<uuid:task_id>/",
        TaskRetrieveUpdateView.as_view(),
        name="project-task-detail"
    ),
    path(
        "workspaces/<uuid:workspace_id>/projects/<uuid:project_id>/tasks/<uuid:task_id>/start/",
        StartTaskView.as_view(),
        name="start-task"
    ),
    path(
        "workspaces/<uuid:workspace_id>/projects/<uuid:project_id>/tasks/<uuid:task_id>/complete/",
        CompleteTaskView.as_view(),
        name="complete-task"
    ),
    path(
        "workspaces/<uuid:workspace_id>/projects/<uuid:project_id>/tasks/<uuid:task_id>/comment/",
        CommentListCreateView.as_view(),
        name="task-comment"
    ),

    # Project members
    path(
        "workspaces/<uuid:workspace_id>/projects/<uuid:project_id>/members/",
        ProjectMemberView.as_view(),
        name="project-members"
    ),
]
