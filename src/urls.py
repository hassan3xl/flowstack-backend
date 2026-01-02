
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.response import Response
from rest_framework.views import APIView
import socket 


class TestView(APIView):
    def get(self, request):
        return Response({
            "message": "Hello!",
            "served_by_container": socket.gethostname() 
        })
    
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('apps.router.urls')),
    # path('test/', TestView.as_view(), name='test'),
] 

# Only load toolbar URLs if DEBUG is True AND the app is installed
if settings.DEBUG:
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns += [
            path('__debug__/', include(debug_toolbar.urls)),
        ]