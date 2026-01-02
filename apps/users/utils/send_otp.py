# utils.py
from django.core.mail import send_mail
from ..models import OTPRequest

def send_otp_email(email):
    otp = OTPRequest.generate_code()
    
    # Save to DB (Update existing or create new)
    OTPRequest.objects.update_or_create(
        email=email,
        defaults={'otp_code': otp, 'is_verified': False}
    )
    
    # Send via Resend
    subject = "Your Verification Code"
    message = f"Your one-time password is: {otp}. It expires in 10 minutes."
    
    send_mail(
        subject,
        message,
        'onboarding@resend.dev', 
        [email],
        fail_silently=False,
    )