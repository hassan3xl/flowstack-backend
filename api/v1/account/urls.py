# urls.py
from django.urls import path
from .views import (
    UserAccountView, 
    UserProfileView,
    UserProfileAvatarView
)

urlpatterns = [
    path("profile/", UserProfileView.as_view(), name="user-profile"),
    path("profile/avatar/", UserProfileAvatarView.as_view(), name="user-profile"),
    path("account/", UserAccountView.as_view(), name="user-account"),

]
