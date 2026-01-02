from django.urls import path

class UserProfileView():
    pass

urlpatterns = [
    path("settings/", UserProfileView, name="user-settings"),
]
