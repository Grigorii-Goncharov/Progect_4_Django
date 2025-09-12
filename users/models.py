from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.validators import EmailValidator
from django.db import models


class UserManager(BaseUserManager):
    """Кастомный менеджер для создания пользователей и суперпользователей.
    Переопределяет стандартные методы создания пользователей, чтобы использовать
    email в качестве уникального идентификатора вместо username.
    """

    def create_user(self, email, password=None, **extra_fields):
        """Создаёт и возвращает обычного пользователя с заданным email и паролем.
        Args:
            email (str): Уникальный email пользователя.
            password (str, optional): Пароль пользователя. Если не указан — создаётся без пароля.
            **extra_fields: Дополнительные поля модели пользователя.
        Returns:
            User: Экземпляр созданного пользователя.
        Raises:
            ValueError: Если email не указан.
        """
        if not email:
            raise ValueError("Email обязателен")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Создаёт и возвращает суперпользователя с правами администратора.
        Автоматически устанавливает is_staff=True и is_superuser=True.
        Args:
            email (str): Уникальный email суперпользователя.
            password (str, optional): Пароль суперпользователя.
            **extra_fields: Дополнительные поля модели.
        Returns:
            User: Экземпляр созданного суперпользователя.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Суперпользователь должен иметь is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Суперпользователь должен иметь is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Кастомная модель пользователя с email в качестве основного идентификатора.
    Расширяет стандартную модель AbstractUser, заменяя username на email для аутентификации.
    Добавляет дополнительные поля: телефон и токен (например, для сброса пароля или API).

    Attributes:
        email (EmailField): Уникальный email пользователя — используется для входа.
        phone (CharField): Номер телефона (до 12 символов).
        token (CharField): Токен для временных операций (например, верификация, сброс пароля).

    Meta:
        verbose_name: "Пользователь"
        verbose_name_plural: "Пользователи"
    """

    username = models.CharField(max_length=50, verbose_name="Никнейм")
    email = models.EmailField(
        unique=True,
        verbose_name="Электронная почта",
        validators=[EmailValidator()],
    )
    phone = models.CharField(max_length=12, verbose_name="Телефон")
    token = models.CharField(
        max_length=120,
        verbose_name="Токен",
        null=True,
        blank=True,
        help_text="Используется для временных операций, например, сброса пароля.",
    )

    USERNAME_FIELD = "email"  # Используем email для аутентификации
    REQUIRED_FIELDS = (
        []
    )  # Поля, обязательные при создании суперпользователя через createsuperuser (кроме email и пароля)

    objects = UserManager()

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
