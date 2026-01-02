from django.urls import path
from ..views.auth_views import GoogleLogin, RequestOTPView, VerifyOTPView, ResetPasswordView
from django.urls import path, include
# Import SimpleJWT views for standard token refresh
from rest_framework_simplejwt.views import TokenVerifyView, TokenRefreshView

urlpatterns = [
    # 1. Standard Auth (Login, Logout, Password Change, User details)
    path('auth/', include('dj_rest_auth.urls')),

    # 2. Registration (Uses your CustomRegisterSerializer)
    path('auth/registration/', include('dj_rest_auth.registration.urls')),

    # 3. Google Auth
    path('auth/google/', GoogleLogin.as_view(), name='google_login'),

    # 4. Token Management (The missing link!)
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # 5. Your Custom OTP Password Reset (Keep your existing views here)
    path('auth/otp/request/', RequestOTPView.as_view(), name='otp_request'),
    path('auth/otp/verify/', VerifyOTPView.as_view(), name='otp_verify'),
    path('auth/password-reset/', ResetPasswordView.as_view(), name='password_reset'),
]