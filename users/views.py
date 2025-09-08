import secrets
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.shortcuts import redirect, render, get_object_or_404
from django.views.generic import CreateView, UpdateView, ListView
from django.views import View
from django.urls import reverse_lazy
from config.settings import EMAIL_HOST_USER
from mailservices.models import MailAttempt, Mailing
from .forms import CustomUserCreationForm, UserProfileForm
from .models import User
from mailservices.models import Recipient, Message


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
    """Вьюшка кабинета пользователя"""

    def get(self, request):
        user = request.user
        attempts = MailAttempt.objects.filter(mailing__owner=user)

        context = {
            "user_profile": user,
            "total_attempts": attempts.count(),
            "successful_attempts": attempts.filter(status="success").count(),
            "failed_attempts": attempts.filter(status="failed").count(),
        }
        return render(request, "users/profile.html", context)


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


class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Просмотр списка пользователей + статистика по сообщениям, клиентам и рассылкам"""
    model = User
    template_name = "users/user_list.html"
    context_object_name = "users"

    # 🔽 Правильно: флаг должен быть атрибутом класса
    raise_exception = True

    def test_func(self):
        """Разрешаем доступ только суперпользователю - для работы UserPassedTestMixin"""
        perms_list = [
            "mailservices.can_view_all_messages",
            "mailservices.can_view_all_clients",
            "mailservices.can_view_all_sendings",
        ]
        return self.request.user.has_perms(perms_list)

    def get_queryset(self):
        """Суперпользователь видит всех, остальные — пустой queryset (доступ запрещён через test_func)"""
        return User.objects.all()  # будет вызвано только если test_func вернул True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Теперь безопасно: мы знаем, что пользователь — суперпользователь
        context['messages_list'] = Message.objects.all()
        context['sendings_list'] = Mailing.objects.all()
        context['clients_list'] = Recipient.objects.all()
        context['title'] = 'Админ-панель: Все данные'

        return context

@login_required
def toggle_user_active(request, pk):
    """Блокировка пользователя админом или модератором"""

    if not request.user.is_superuser:
        return redirect('users:user_list')

    user = get_object_or_404(User, pk=pk)

    # Защита от самоблокирования
    if user.pk == request.user.pk:
        messages.error(request, "Нельзя заблокировать самого себя!")
        return redirect('users:user_list')

    #  Переключаем статус
    user.is_active = not user.is_active
    user.save()

    # 📢 Оповещение — что изменилось
    if user.is_active:
        messages.success(request, f"Пользователь {user.username} разблокирован.")
    else:
        messages.warning(request, f"Пользователь {user.username} заблокирован.")

    return redirect('users:user_list')


