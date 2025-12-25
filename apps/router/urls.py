# urls.py
from django.urls import path, include
from apps.users.api.routes import auth_urls
from apps.workspace.api.routes import workspace_urls, project_urls
from apps.community.api.routes import community_urls, posts_urls
from apps.users.api.routes import auth_urls, user_urls, settings_urls
from apps.notifications.api.routes import urls as notifications_url

urlpatterns = [
    path('auth/', include(auth_urls)),
    # community urls
    path('', include(community_urls)),

    # workspace urls
    path('', include(workspace_urls)),

    # projects url
    path('', include(project_urls)),
    
    # feeds url
    path('posts/', include(posts_urls)),


    path('settings/', include(settings_urls)),
    path('notifications/', include(notifications_url)),
    path('user/', include(user_urls)),

]