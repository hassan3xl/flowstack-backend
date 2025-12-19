# urls/api.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ..views import views

# router = DefaultRouter()
# router.register(r'notifications', views.NotificationViewSet, basename='notification')
# router.register(r'preferences', views.UserNotificationPreferenceViewSet, basename='preference')
# router.register(r'templates', views.NotificationTemplateViewSet, basename='template')

urlpatterns = [
    # path('', include(router.urls)),
    
    # Additional API endpoints
    path('', views.NotificationsList.as_view(), name='notifications-list'),

    # path('notifications/bulk/mark-read/', views.BulkMarkAsReadView.as_view(), name='bulk-mark-read'),
    # path('notifications/bulk/delete/', views.BulkDeleteNotificationsView.as_view(), name='bulk-delete'),
    # path('notifications/stats/summary/', views.NotificationSummaryView.as_view(), name='notification-summary'),
]