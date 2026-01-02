# models.py
from django.db import models
from django.utils import timezone
import secrets

class OTPRequest(models.Model):
    email = models.EmailField()
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def is_valid(self):
        # Valid if created within last 10 minutes
        now = timezone.now()
        time_diff = now - self.created_at
        return time_diff.total_seconds() < 600  # 600 seconds = 10 mins

    @staticmethod
    def generate_code():
        return f"{secrets.randbelow(1000000):06d}"