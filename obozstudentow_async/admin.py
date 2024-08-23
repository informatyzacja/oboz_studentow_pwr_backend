from django.contrib import admin

# Register your models here.
from .models import *

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'date', 'chat')
    list_filter = ('chat',)

@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('name','enabled', 'user_count')
    list_filter = ('enabled','users')

    filter_horizontal = ('users','blocked_by','notifications_blocked_by')

    def user_count(self, obj):
        return obj.users.count()
    user_count.short_description = 'Liczba użytkowników'
