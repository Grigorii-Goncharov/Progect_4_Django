from django.contrib import admin
from .models import Recipient, Message

@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'full_name', 'owner')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'mail_title', 'owner',)
    list_filter = ('owner',)
    search_fields = ('mail_title',)
