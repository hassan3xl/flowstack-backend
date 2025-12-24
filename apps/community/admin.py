from django.contrib import admin
from .models import(
    Community,
    CommunityCategory,
    CommunityMember,
    CommunityInvitation,
    CommunityChannel,
    Post,
    Comment, 
    PostLike
)

admin.site.register(Community)
admin.site.register(CommunityCategory)
admin.site.register(CommunityMember)
admin.site.register(CommunityInvitation)
admin.site.register(CommunityChannel)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(PostLike)