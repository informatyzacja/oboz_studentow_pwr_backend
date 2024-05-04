from django.contrib import admin

# Register your models here.
from .models import *

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'date', 'chat')
    list_filter = ('chat',)

@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('name',)
    filter_horizontal = ('users',)