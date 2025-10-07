from rest_framework_simplejwt.authentication import JWTAuthentication

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # 1. Try normal Authorization header
        header = self.get_header(request)
        if header:
            raw_token = self.get_raw_token(header)
            if raw_token:
                validated_token = self.get_validated_token(raw_token)
                return self.get_user(validated_token), validated_token

        # 2. If no header, try cookie
        raw_token = request.COOKIES.get("access_token")
        if raw_token:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token

        return None
