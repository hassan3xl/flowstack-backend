from django.urls import path
from ..views.auth_views import RegisterView, LoginView

urlpatterns = [
    path("signup/", RegisterView.as_view(), name="register"),
    path("signin/", LoginView.as_view(), name="signin"),
]
