from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from user_manager.models import CustomUser, UserProfile
from .serializers import AccountProfileSerializer, AccountUserSerializer
from django.utils import timezone


class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AccountProfileSerializer

    def get_object(self):
        return self.request.user.profile

    
class UserProfileAvatarView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    serializer_class = AccountProfileSerializer

    def get_object(self):
        return self.request.user.profile

    def patch(self, request, *args, **kwargs):
        """
        Allows PATCH for avatar only:
        { "avatar": <file> }
        """
        return super().patch(request, *args, **kwargs)


class UserAccountView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AccountUserSerializer

    def get_object(self):
        return self.request.user


class UserAccountSuspendView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        user = request.user
        user.is_active = False
        user.save()
        return Response({"detail": "Account suspended."}, status=status.HTTP_200_OK)
    
class UserAccountDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def delete(self, request, *args, **kwargs):
        user = request.user
        user.delete()
        return Response({"detail": "Account deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
