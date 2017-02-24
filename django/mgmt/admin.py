from django.contrib import admin
from .models import SystemNotice, BlogPost


class SystemNoticeAdmin(admin.ModelAdmin):
    model = SystemNotice

admin.site.register(SystemNotice, SystemNoticeAdmin)

class SystemBlogPost(admin.ModelAdmin):
    model = BlogPost

admin.site.register(BlogPost, SystemBlogPost)

