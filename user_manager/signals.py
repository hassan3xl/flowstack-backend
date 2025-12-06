from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .utils.generate_username import generate_flow_username
from .models import UserProfile
User = get_user_model()

@receiver(post_save, sender=UserProfile)
def assign_default_username(sender, instance, created, **kwargs):
    if created:
        if not instance.username:  # Only set if user has no username
            instance.username = generate_flow_username()
            instance.save(update_fields=["username"])
