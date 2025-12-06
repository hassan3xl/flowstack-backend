from django.db.models.signals import post_save
from django.dispatch import receiver
from server_manager.models import Server
from .models import ServerInvitation, generate_invite_code

@receiver(post_save, sender=Server)
def create_server_invite(sender, instance, created, **kwargs):
    if created:
        ServerInvitation.objects.create(server=instance, invite_code=generate_invite_code())