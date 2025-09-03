# forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from .bad_words import FORBIDDEN_WORDS
from .models import Recipient


class RecipientForm(forms.ModelForm):
    class Meta:
        model = Recipient
        fields = ['email', 'full_name', 'comment', ]

    def __init__(self, *args, **kwargs):
        super(RecipientForm, self).__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Email пользователя'})

        self.fields['full_name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Фамилия Имя Отчество'})

        self.fields['comment'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Информация о пользователе'})

    def clean_email(self):
        """Метод проверки на email на корректность и его уникальность в Базе данных"""
        email = self.cleaned_data.get("email")
        if email:
            try:
                validate_email(email)
            except ValidationError:
                raise forms.ValidationError("Введите корректный email-адрес.")

            # Проверка уникальности email (кроме текущего пользователя)
            if Recipient.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
                raise forms.ValidationError("Этот email уже используется.")
        return email

    def clean_full_name(self):
        """Метод проверки ФИО """
        full_name = self.cleaned_data.get('full_name')

        if full_name:

            full_name_stripped = full_name.strip()

            if not full_name_stripped.replace(' ', '').isalpha():
                raise ValidationError('Имя должно состоять только из букв и пробелов.')

            if not full_name_stripped:
                raise ValidationError('Имя не может быть пустым или состоять только из пробелов.')
        else:
            raise ValidationError('Имя обязательно для заполнения.')
        return full_name

    def clean_comment(self):
        """Валидатор корректности описания"""
        comment = self.cleaned_data.get('comment', '')
        if not comment.strip():
            return comment

        lower_comment = comment.lower()
        for word in FORBIDDEN_WORDS:
            if word in lower_comment:
                raise ValidationError(f'Недопустимое слово: "{word}"!')
        return comment



