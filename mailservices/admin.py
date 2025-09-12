from django.contrib import admin
from .models import Recipient, Message, Mailing


@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    """Административный интерфейс для управления получателями рассылок.
    Позволяет просматривать и редактировать данные получателей: email, ФИО, владельца.
    """

    list_display = ("id", "email", "full_name", "owner")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Административный интерфейс для управления сообщениями рассылок.
    Позволяет фильтровать по владельцу, искать по заголовку.
    """

    list_display = ("id", "mail_title", "owner")
    list_filter = ("owner",)
    search_fields = ("mail_title",)


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    """Административный интерфейс для управления рассылками.
    Позволяет фильтровать по владельцу, статусу и временным рамкам.
    Поддерживается поиск по заголовку сообщения (если поле mail_title доступно через связь).
    """

    list_display = ("id", "start_datetime", "end_datetime", "status")
    list_filter = ("owner", "start_datetime", "end_datetime", "status")
    search_fields = ("message__mail_title",)  # Исправлено: поиск по связанному полю
