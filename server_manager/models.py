from django.db import models
from django.utils import timezone
import uuid
from user_manager.models import CustomUser as User
import secrets
def generate_invite_code():
    # 12-character URL-safe, cryptographically secure
    return secrets.token_urlsafe(9)  # ~12 chars

class ServerCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


    
class Server(models.Model):
    SERVER_TYPES = (
        ('public', 'Public'),
        ('private', 'Private'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.ImageField(upload_to='server_icons/', null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_servers')
    server_type = models.CharField(max_length=10, choices=SERVER_TYPES, default='private')
    category = models.ForeignKey(ServerCategory, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    member_count = models.IntegerField(default=1)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class ServerMember(models.Model):
    ROLE_CHOICES = (
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('moderator', 'Moderator'),
        ('member', 'Member'),
    )
    
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='server_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('server', 'user')
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.user.email} in {self.server.name} - {self.role}"



class ServerInvitation(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    )

    ROLE_CHOICES = (
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('moderator', 'Moderator'),
        ('member', 'Member'),
    )
    

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Link to the server
    server = models.ForeignKey(
        Server,
        on_delete=models.CASCADE,
        related_name='invitations'
    )

    # Who created the invite (optional)
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='sent_invitations',
        null=True,
        blank=True
    )

    # If invite was targeted to a specific user
    invited_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='received_invitations',
        null=True,
        blank=True
    )

    # The invite link code
    invite_code = models.CharField(
        max_length=32,
        unique=True,
        db_index=True
    )

    # Status
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
 

    # Usage limits
    max_uses = models.IntegerField(default=1)  # 0 = unlimited
    uses = models.IntegerField(default=0)

    # Expiration settings
    expires_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Invite for {self.server.name} - {self.status} - {self.role}"

    # --------------- VALIDATION ------------------

    @property
    def is_expired(self):
        if self.expires_at and self.expires_at < timezone.now():
            return True
        return False


        #  SAVE OVERRIDE 

    def save(self, *args, **kwargs):
        if not self.invite_code:
            self.invite_code = generate_invite_code()
        if self.is_expired:
            self.status = 'expired'
        super().save(*args, **kwargs)



class Channel(models.Model):
    CHANNEL_TYPES = (
        ('text', 'Text Channel'),
        ('announcement', 'Announcement'),
        ('voice', 'Voice Channel'),  # Future feature
    )
    
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name='channels')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    channel_type = models.CharField(max_length=20, choices=CHANNEL_TYPES, default='text')
    is_private = models.BooleanField(default=False)
    position = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Permissions
    allowed_roles = models.JSONField(default=list, blank=True)  # ['admin', 'moderator']
    
    class Meta:
        ordering = ['position', 'name']

class Message(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    attachments = models.JSONField(default=list, blank=True)
    reply_to = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)