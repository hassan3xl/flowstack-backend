# urls.py
from django.urls import path, include
from api.v1.auth import urls as auth_urls
from api.v1.projects import urls as project_urls
from api.v1.user_settings import urls as settings_url
from api.v1.account import urls as account_url
from api.v1.notifications import urls as notifications_url
from api.v1.server import urls as server_url
from api.v1.feeds import urls as feeds_url


urlpatterns = [
    path('auth/', include(auth_urls)),
    # server urls
    path('', include(server_url)),
    # projects url
    path('', include(project_urls)),
    # feeds url
    path('feeds/', include(feeds_url)),
    path('settings/', include(settings_url)),
    path('notifications/', include(notifications_url)),
    path('user/', include(account_url)),

]