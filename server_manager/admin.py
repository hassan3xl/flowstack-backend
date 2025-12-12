from django.contrib import admin
from .models import Server, ServerInvitation, ServerMember, ServerCategory

admin.site.register(Server)
admin.site.register(ServerInvitation)
admin.site.register(ServerMember)
admin.site.register(ServerCategory)



# Register your models here.
