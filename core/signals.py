from django.dispatch import receiver
from django.db.models.signals import post_save
from notifications.models import Notification, NotificationTemplate
from core.models import CustomUser

@receiver(post_save, sender=CustomUser)
def send_signup_notification(sender, instance, created, **kwargs):
    if created:
        # Get template
        template = NotificationTemplate.objects.filter(name="signup_welcome", is_active=True).first()
        if not template:
            return

        # Replace placeholders in message
        message = template.message.replace("{{user.profile.first_name}}",  instance.email)
        html_message = template.html_message.replace("{{user..profile.first_name}}",  instance.email)

        # Create notification record
        Notification.objects.create(
            user=instance,
            template=template,
            title="Welcome to MyApp",
            message=message,
            html_message=html_message,
            channels=template.channels,
            category="signup",
        )
