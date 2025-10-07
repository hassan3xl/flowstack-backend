# urls.py
from django.urls import path, include
from api.auth import urls as auth_urls
from api.user_projects import urls as project_urls
from api.dashboard import urls as dashboard_url
from api.user_settings import urls as settings_url
from api.users import urls as users_url



urlpatterns = [
    path('auth/', include(auth_urls)),
    path('dashboard/', include(dashboard_url)),
    path('projects/', include(project_urls)),
    path('settings/', include(settings_url)),
    path('users/', include(users_url)),


]