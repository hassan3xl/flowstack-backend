from rest_framework_nested import routers
from django.urls import path, include

from .views import ProjectViewSet, ProjectItemListCreateView, ProjectItemRetriveUpdateView

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
        "servers/<uuid:server_id>/projects/<uuid:project_id>/items/<uuid:item_id>/update/", 
         ProjectItemRetriveUpdateView.as_view(), 
         name="project-items"),

    # path("", include(projects_router.urls)),
]
