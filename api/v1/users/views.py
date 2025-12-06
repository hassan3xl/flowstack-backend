# views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from user_manager.models import CustomUser, UserProfile
from .serializers import UserSerializer, UserProfileSerializer, UserPublicSerializer


class UserPublicProfileView(generics.RetrieveAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserPublicSerializer
    permission_classes = [permissions.IsAuthenticated]  
    lookup_field = "id" 


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for users to view and manage their profiles
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # For profile picture uploads

    def get_object(self):
        """
        Return the current authenticated user
        """
        return self.request.user

    def get_serializer_class(self):
        """
        Use different serializers for GET vs PUT/PATCH requests
        """
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer  # We'll create this below
        return UserSerializer

    def update(self, request, *args, **kwargs):
        """
        Handle profile updates, including nested profile data
        """
        user = self.get_object()
        
        # Handle partial updates
        partial = kwargs.pop('partial', False)
        
        # Update user fields (if any writable fields exist)
        user_serializer = self.get_serializer(user, data=request.data, partial=partial)
        user_serializer.is_valid(raise_exception=True)
        
        # Update profile fields
        profile_data = request.data.get('profile', {})
        if profile_data:
            profile_serializer = UserProfileSerializer(
                user.profile, 
                data=profile_data, 
                partial=partial,
                context={'request': request}
            )
            profile_serializer.is_valid(raise_exception=True)
            profile_serializer.save()
        
        user_serializer.save()
        
        return Response(user_serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """
        Get user profile with detailed information
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)





# Optional: View for users to delete their account
class UserDeleteAccountView(generics.DestroyAPIView):
    """
    API endpoint for users to delete their account
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        
        # You might want to add additional checks here
        # For example, check if user has any important data before deletion
        
        user.delete()
        return Response(
            {"detail": "Account deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )


# Optional: View for users to change their password
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import update_session_auth_hash
from rest_framework.permissions import IsAuthenticated

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Custom endpoint for changing password
    """
    serializer = PasswordChangeSerializer(data=request.data)
    
    if serializer.is_valid():
        user = request.user
        old_password = serializer.validated_data['old_password']
        new_password = serializer.validated_data['new_password']
        
        if not user.check_password(old_password):
            return Response(
                {"old_password": ["Wrong password."]}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.save()
        
        # Keep user logged in after password change
        update_session_auth_hash(request, user)
        
        return Response({"detail": "Password updated successfully."})
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
