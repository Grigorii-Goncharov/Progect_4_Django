from django.contrib import admin

from users.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Административный интерфейс для управления пользователями.
    Отображает основные поля пользователя в списке: email и телефон.
    Позволяет администратору просматривать, редактировать и управлять учетными записями пользователей.
    Attributes:
        list_display (tuple): Поля, отображаемые в списке пользователей — email и phone.
    """

    list_display = ("email", "phone")
