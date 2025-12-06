from django.urls import path
from .views import RegisterView, LoginView, UserDetailsView

urlpatterns = [
    path("signup/", RegisterView.as_view(), name="register"),
    path("signin/", LoginView.as_view(), name="signin"),
    path("profile/", UserDetailsView.as_view(), name="user-profile"),
]
