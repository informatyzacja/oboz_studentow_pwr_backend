from django.contrib import admin

# Register your models here.
from .models import Message

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'date', 'group_name')
    list_filter = ('group_name',)