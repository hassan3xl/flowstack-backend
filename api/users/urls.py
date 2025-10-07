# urls.py
from django.urls import path
from .views import UserPublicProfileView

urlpatterns = [
    path("<uuid:id>/", UserPublicProfileView.as_view(), name="user-public-profile"),
]
