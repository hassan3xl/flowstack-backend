from django.contrib import admin
from .models import Server, ServerInvitation, ServerMember

admin.site.register(Server)
admin.site.register(ServerInvitation)
admin.site.register(ServerMember)


# Register your models here.
