from django.contrib import admin
from .models import Recipient, Message, Mailing


@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    """получатель рассылки"""

    list_display = ("id", "email", "full_name", "owner")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Сообщение"""

    list_display = (
        "id",
        "mail_title",
        "owner",
    )
    list_filter = ("owner",)
    search_fields = ("mail_title",)


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    """Сообщение"""

    list_display = (
        "id",
        "start_datetime",
        "end_datetime",
        "status",
    )
    list_filter = (
        "owner",
        "start_datetime",
        "end_datetime",
        "status",
    )
    search_fields = ("mail_title",)
