from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from apps.users.api import (
AccountProfileSerializer, AccountUserSerializer, AccountProfileAvatarSerializer
)
from django.utils import timezone
from users.models import Profile


# catching
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

# rate limiting
from rest_framework.throttling import ScopedRateThrottle

class PublicUserProfileView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = AccountProfileSerializer
    lookup_field = "username"

    queryset = Profile.objects.select_related("user")

    @method_decorator(cache_page(60 * 10))  # SAFE
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AccountProfileSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'sensitive_action'

    def get_object(self):
        return self.request.user.profile

    def get(self, request, *args, **kwargs):
        cache_key = f"user_profile:{request.user.id}"

        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        response = super().get(request, *args, **kwargs)

        cache.set(cache_key, response.data, timeout=300)
        return response

    def put(self, request, *args, **kwargs):
        response = super().put(request, *args, **kwargs)
        cache.delete(f"user_profile:{request.user.id}")
        return response



class UserAccountView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AccountUserSerializer
    
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'sensitive_action'

    def get_object(self):
        return self.request.user

    def get(self, request, *args, **kwargs):
        cache_key = f"user_account:{request.user.id}"

        data = cache.get(cache_key)
        if data:
            return Response(data)

        response = super().get(request, *args, **kwargs)
        cache.set(cache_key, response.data, 300)
        return response

    def put(self, request, *args, **kwargs):
        response = super().put(request, *args, **kwargs)
        cache.delete(f"user_account:{request.user.id}")
        return response


class UserProfileAvatarView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    serializer_class = AccountProfileAvatarSerializer

    def get_object(self):
        return self.request.user.profile


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
        cache.delete(f"user_profile:{user.id}")
        cache.delete(f"user_account:{user.id}")
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

