from django.contrib import admin
from .models import Feed, FeedComment, FeedLike

admin.site.register(Feed)
admin.site.register(FeedComment)
admin.site.register(FeedLike)

# Register your models here.
