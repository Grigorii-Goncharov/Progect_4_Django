import secrets
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.shortcuts import redirect, render, get_object_or_404
from django.views.generic import CreateView, UpdateView
from django.views import View
from django.urls import reverse_lazy
from config.settings import EMAIL_HOST_USER
from .forms import CustomUserCreationForm, UserProfileForm
from .models import User


class UserRegisterView(CreateView):
    """Представление для регистрации нового пользователя.
    Обрабатывает форму регистрации, генерирует токен подтверждения,
    отправляет письмо с ссылкой для активации аккаунта.
    """

    form_class = CustomUserCreationForm
    template_name = "users/register.html"
    success_url = reverse_lazy("users:login")

    def form_valid(self, form):
        """Сохраняет пользователя как неактивного, генерирует токен и отправляет письмо подтверждения.
        Args:
            form (CustomUserCreationForm): Валидная форма регистрации.
        Returns:
            HttpResponse: Перенаправление на страницу входа.
        """
        user = form.save(commit=False)  # Сохраняем пользователя без логирования
        user.is_active = False  # Деактивируем
        token = secrets.token_hex(16)  # Генерация токена
        user.token = token
        user.save()

        host = self.request.get_host()
        url = f"http://{host}/users/email-confirm/{token}/"
        send_mail(
            subject="Подтверждение почты при регистрации аккаунта",
            message=f"Перейдите по ссылке {url} для завершения регистрации",
            from_email=EMAIL_HOST_USER,
            recipient_list=[user.email],
        )

        messages.info(
            self.request, "Письмо подтверждения регистрации направлено на почту"
        )
        return redirect(self.success_url)


def email_verification(request, token):
    """Обрабатывает подтверждение email по токену.

    Активирует пользователя, если токен верный. Если пользователь уже активен,
    перенаправляет на страницу входа.
    Args:
        request (HttpRequest): Запрос от пользователя.
        token (str): Уникальный токен подтверждения.
    Returns:
        HttpResponse: Перенаправление на страницу входа.
    """
    user = get_object_or_404(User, token=token)

    if user.is_active:
        # Уже активен — просто перенаправляем
        messages.info(request, "Ваш email уже подтверждён. Вы можете войти.")
        return redirect("users:login")

    # Активируем
    user.is_active = True
    user.token = None  # Обнуляем токен, чтобы можно было использовать его для сброса пароля позже
    user.save()

    messages.success(request, "Email подтверждён! Теперь можно войти.")
    return redirect("users:login")


class UserProfileView(View):
    """Представление для отображения профиля пользователя.
    Требует аутентификации (через middleware или декораторы).
    Отображает страницу профиля.
    """

    def get(self, request):
        """Отображает страницу профиля пользователя.
        Args:
            request (HttpRequest): GET-запрос от пользователя.
        Returns:
            HttpResponse: Отрендеренная страница профиля.
        """
        return render(request, "users/profile.html")


class UserLoginView(LoginView):
    """Представление для входа пользователя в систему.
    Использует стандартный LoginView Django с кастомным шаблоном.
    """

    template_name = "users/login.html"


class UserProfileEditView(LoginRequiredMixin, UpdateView):
    """Представление для редактирования профиля пользователя.
    Позволяет авторизованному пользователю изменить свои данные профиля.
    """

    form_class = UserProfileForm
    template_name = "users/profile_edit.html"
    success_url = reverse_lazy("users:profile")

    def get_object(self, queryset=None):
        """Возвращает объект пользователя, который будет редактироваться.
        В данном случае — всегда текущий аутентифицированный пользователь.
        Args:
            queryset (QuerySet, optional): Набор объектов. По умолчанию None.
        Returns:
            User: Объект текущего пользователя.
        """
        return self.request.user  # редактируем только текущего пользователя


from django.shortcuts import render
