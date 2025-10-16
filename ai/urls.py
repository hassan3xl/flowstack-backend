from django.urls import path
from .views import HuggingFaceChatView

urlpatterns = [
    path("chat/", HuggingFaceChatView.as_view(), name="chat_with_ai"),
]
