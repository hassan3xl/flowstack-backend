from django.urls import path
from .views import UserDashboardAPIView

urlpatterns = [
    path('', UserDashboardAPIView.as_view(), name='user-dashboard'),
]