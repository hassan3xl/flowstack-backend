from django.urls import path
from .views import RegisterView, LoginView, UserDetailsView

urlpatterns = [
    path("signup/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("user/", UserDetailsView.as_view(), name="user-details"),
]
