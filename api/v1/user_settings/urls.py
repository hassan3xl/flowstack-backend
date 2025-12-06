# urls.py
from django.urls import path
from . import views

urlpatterns = [
    
    path('', views.UserSettingsView.as_view(), name='user-settings'),
]