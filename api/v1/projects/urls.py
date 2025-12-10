from rest_framework_nested import routers
from django.urls import path, include

from .views import (
    ProjectViewSet, 
    ProjectItemListCreateView, 
    ProjectItemRetriveUpdateView,
    CollabView,
    StartTaskView,
    CompleteTaskView,
    CommentListCreateView,
)

router = routers.SimpleRouter()
# server/<server_id>/projects/
router.register(r'servers/(?P<server_id>[^/.]+)/projects', ProjectViewSet, basename='server-projects')

projects_router = routers.NestedSimpleRouter(
    router, 
    r'servers/(?P<server_id>[^/.]+)/projects', 
    lookup='project'
)
# projects_router.register(r'items', ProjectItemViewSet, basename='project-items')

urlpatterns = [
    path("", include(router.urls)),
    path("servers/<uuid:server_id>/projects/<uuid:project_id>/items/", ProjectItemListCreateView.as_view(), name="project-items"),
    path(
        "servers/<uuid:server_id>/projects/<uuid:project_id>/items/<uuid:item_id>/", 
        ProjectItemRetriveUpdateView.as_view(), 
        name="project-items"
    ),
    path(
        "servers/<uuid:server_id>/projects/<uuid:project_id>/items/<uuid:item_id>/start/", 
        StartTaskView.as_view(), 
        name='start-task'
    ),
    path(
        "servers/<uuid:server_id>/projects/<uuid:project_id>/items/<uuid:item_id>/comment/", 
        CommentListCreateView.as_view(), 
        name='comment'
    ),
    path(
        "servers/<uuid:server_id>/projects/<uuid:project_id>/items/<uuid:item_id>/complete/", 
        CompleteTaskView.as_view(),
        name="complete"
    ),
    path(
        "servers/<uuid:server_id>/projects/<uuid:project_id>/add-collab/", 
        CollabView.as_view(), 
        name="add-collab"
    ),

]
