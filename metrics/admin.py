# metrics/admin.py
from django.contrib import admin
from .models import PageView, UserAction

@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    list_display = ('user', 'path', 'method', 'timestamp', 'ip_address')
    list_filter = ('timestamp', 'method', 'user')
    search_fields = ('user__username', 'path', 'ip_address')
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)

@admin.register(UserAction)
class UserActionAdmin(admin.ModelAdmin):
    list_display = ('user', 'action_type', 'timestamp', 'content_object')
    list_filter = ('timestamp', 'action_type', 'user')
    search_fields = ('user__username', 'action_type')
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)