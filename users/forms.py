from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from users.models import User


class CustomUserCreationForm(UserCreationForm):
    """Форма регистрации нового пользователя с использованием email в качестве логина.
    Расширяет стандартную форму UserCreationForm, добавляя поля email и phone.
    Включает кастомную валидацию:
        - email проверяется на корректный формат.
        - phone должен содержать только цифры.
    Aтрибуты:
        username (CharField): Никнейм пользователя.
        email (EmailField): Уникальный email (используется для входа).
        phone (CharField): Номер телефона (только цифры).
    """

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["email", "username", "phone"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем Bootstrap-классы и плейсхолдеры
        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Введите имя пользователя"}
        )
        self.fields["email"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Введите email"}
        )
        self.fields["phone"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Введите телефон (только цифры)"}
        )

    def clean_phone(self):
        """Валидация поля 'phone': разрешены только цифры.
        Returns:
            str: Очищенное значение номера телефона.
        Raises:
            ValidationError: Если номер содержит нецифровые символы.
        """
        phone = self.cleaned_data.get("phone")
        if phone and not phone.isdigit():
            raise forms.ValidationError("Номер телефона должен содержать только цифры.")
        return phone

    def clean_email(self):
        """Валидация поля 'email': проверка формата и уникальности.
        Returns:
            str: Очищенное значение email.
        Raises:
            ValidationError: Если email некорректен или уже зарегистрирован.
        """
        email = self.cleaned_data.get("email")
        if email:
            try:
                validate_email(email)
            except ValidationError:
                raise forms.ValidationError("Введите корректный email-адрес.")

            # Проверка уникальности email
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError(
                    "Пользователь с таким email уже существует."
                )
        return email


class UserProfileForm(forms.ModelForm):
    """Форма редактирования профиля пользователя (без изменения пароля).
    Позволяет обновлять username, email и phone.
    Включает кастомную валидацию:
        - email проверяется на корректность и уникальность (кроме текущего пользователя).
        - phone должен содержать только цифры.
    Attributes:
        username (CharField): Никнейм пользователя.
        email (EmailField): Уникальный email.
        phone (CharField): Номер телефона.
    """

    class Meta:
        model = User
        fields = ["username", "email", "phone"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем Bootstrap-классы и плейсхолдеры
        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Введите имя пользователя"}
        )
        self.fields["email"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Введите email"}
        )
        self.fields["phone"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Введите телефон (только цифры)"}
        )

    def clean_phone(self):
        """Валидация поля 'phone': разрешены только цифры.
        Returns:
            str: Очищенное значение номера телефона.
        Raises:
            ValidationError: Если номер содержит нецифровые символы.
        """
        phone = self.cleaned_data.get("phone")
        if phone and not phone.isdigit():
            raise forms.ValidationError("Номер телефона должен содержать только цифры.")
        return phone

    def clean_email(self):
        """Валидация поля 'email': проверка формата и уникальности (кроме текущего пользователя).
        Returns:
            str: Очищенное значение email.
        Raises:
            ValidationError: Если email некорректен или уже используется другим пользователем.
        """
        email = self.cleaned_data.get("email")
        if email:
            try:
                validate_email(email)
            except ValidationError:
                raise forms.ValidationError("Введите корректный email-адрес.")

            # Проверка уникальности, исключая текущего пользователя
            if User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
                raise forms.ValidationError("Этот email уже используется.")
        return email
