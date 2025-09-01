from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.validators import EmailValidator, MaxLengthValidator
from django.db import models

# 1. Сначала — кастомный менеджер
class UserManager(BaseUserManager):
    '''Кастомное правило создание пользователя и суперпользователя'''
    def create_user(self, email, password=None, **extra_fields):
        # Проверяем, что email передан
        if not email:
            raise ValueError('Email обязателен')
        email = self.normalize_email(email)# MrJakcon@YanDex.Ru > MrJakcon@yandex.ru
        user = self.model(email=email, **extra_fields)# ← Создаём объект пользователя
        user.set_password(password)# Создаем пароль и хэшируем для безопасности
        user.save(using=self._db)# Сохраняем пользователя и даем атрибут если у вас несколько БД
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    '''Кастомная модель пользователя'''
    username = models.CharField(max_length=50, verbose_name='Никнейм')
    email = models.EmailField(unique=True, verbose_name='Электронная почта',validators=[EmailValidator()])
    phone = models.CharField(max_length=12, verbose_name='Телефон',validators=[MaxLengthValidator(12)])
    token = models.CharField(max_length=120, verbose_name='Токен', null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    # Подключаем наш кастомный менеджер → теперь Django не строит объект из модели, а берет "правило"
    objects = UserManager()

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = ("Пользователь")
        verbose_name_plural = ("Пользователи")