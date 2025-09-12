from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
    DetailView,
)
from django.urls import reverse_lazy

from users.models import User
from .forms import RecipientForm, MessageForm, MailingForm
from .models import Mailing, Recipient, Message, MailAttempt
from .services import send_mailing


def home_view(request):
    """Отображает главную страницу с общей и персональной статистикой по рассылкам.
    Показывает:
        - Общее количество рассылок.
        - Количество активных рассылок (со статусом 'created' или 'started').
        - Уникальное количество получателей.
        - Для авторизованных пользователей — их личные показатели.
    Args:
        request (HttpRequest): Объект запроса от клиента.
    Returns:
        HttpResponse: HTML-страница с контекстом статистики.
    """
    total_mailings = Mailing.objects.count()
    unique_recipients = Recipient.objects.count()
    active_mailings = Mailing.objects.filter(status__in=["created", "started"]).count()

    my_total = my_active = 0
    if request.user.is_authenticated:
        my_total = Mailing.objects.filter(owner=request.user).count()
        my_active = Mailing.objects.filter(
            owner=request.user, status__in=["created", "started"]
        ).count()

    context = {
        "total_mailings": total_mailings,
        "active_mailings": active_mailings,
        "unique_recipients": unique_recipients,
        "my_total": my_total,
        "my_active": my_active,
    }
    return render(request, "mailservices/home.html", context)


# === Recipient Views ===


class RecipientListView(LoginRequiredMixin, ListView):
    """Отображает список получателей, принадлежащих текущему пользователю.
    Администратор видит всех получателей. Обычный пользователь — только свои.
    """

    model = Recipient
    template_name = "mailservices/recipient_list.html"
    context_object_name = "recipients"

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Recipient.objects.all()
        return Recipient.objects.filter(owner=self.request.user)


class RecipientCreateView(LoginRequiredMixin, CreateView):
    """Создаёт нового получателя и привязывает его к текущему пользователю."""

    model = Recipient
    form_class = RecipientForm
    template_name = "mailservices/recipient_form.html"
    success_url = reverse_lazy("mailservices:recipient_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class RecipientDetailView(LoginRequiredMixin, DetailView):
    """Отображает детальную информацию о конкретном получателе.
    Доступ только владельцу записи или администратору.
    """

    model = Recipient
    context_object_name = "recipient"


class RecipientUpdateView(LoginRequiredMixin, UpdateView):
    """Обновляет данные существующего получателя.
    Доступ только владельцу записи или администратору.
    """

    model = Recipient
    fields = ["email", "full_name", "comment"]
    template_name = "mailservices/recipient_form.html"
    success_url = reverse_lazy("mailservices:recipient_list")


class RecipientDeleteView(LoginRequiredMixin, DeleteView):
    """Удаляет получателя после подтверждения.
    Доступ только владельцу записи или администратору.
    """

    model = Recipient
    template_name = "mailservices/recipient_confirm_delete.html"
    success_url = reverse_lazy("mailservices:recipient_list")


# === Message Views ===


class MessageListView(LoginRequiredMixin, ListView):
    """Отображает список сообщений для рассылок.
    Администратор видит все сообщения. Обычный пользователь — только свои.
    """

    model = Message
    template_name = "mailservices/message_list.html"
    context_object_name = "messages"

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Message.objects.all()
        return Message.objects.filter(owner=self.request.user)


class MessageCreateView(LoginRequiredMixin, CreateView):
    """Создаёт новое сообщение для рассылок и привязывает его к текущему пользователю."""

    model = Message
    form_class = MessageForm
    template_name = "mailservices/message_form.html"
    success_url = reverse_lazy("mailservices:message_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MessageUpdateView(LoginRequiredMixin, UpdateView):
    """Обновляет существующее сообщение для рассылки.
    Доступ только владельцу записи или администратору.
    """

    model = Message
    form_class = MessageForm
    template_name = "mailservices/message_form.html"
    success_url = reverse_lazy("mailservices:message_list")


class MessageDeleteView(LoginRequiredMixin, DeleteView):
    """Удаляет сообщение для рассылки после подтверждения.
    Доступ только владельцу записи или администратору.
    """

    model = Message
    template_name = "mailservices/message_confirm_delete.html"
    success_url = reverse_lazy("mailservices:message_list")


class MessageDetailView(LoginRequiredMixin, DetailView):
    """Отображает детальную информацию о сообщении для рассылки.
    Доступ только владельцу записи или администратору.
    """

    model = Message
    context_object_name = "message"


# === Mailing Views ===


class MailingListView(LoginRequiredMixin, ListView):
    """Отображает список рассылок текущего пользователя.
    Автоматически завершает просроченные рассылки со статусом 'started'.
    """

    model = Mailing
    template_name = "mailservices/mailing_list.html"
    context_object_name = "mailings"

    def get_queryset(self):
        now = timezone.now()
        # Автоматически завершаем просроченные рассылки
        Mailing.objects.filter(
            owner=self.request.user, status="started", end_datetime__lt=now
        ).update(status="completed")

        return Mailing.objects.filter(owner=self.request.user).select_related("message")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["now"] = timezone.now()
        return context


class MailingCreateView(LoginRequiredMixin, CreateView):
    """Создаёт новую рассылку и привязывает её к текущему пользователю.
    Ограничивает выбор сообщения и получателей только теми, что принадлежат пользователю.
    """

    model = Mailing
    form_class = MailingForm
    template_name = "mailservices/mailing_form.html"
    success_url = reverse_lazy("mailservices:mailing_list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["message"].queryset = Message.objects.filter(
            owner=self.request.user
        )
        form.fields["recipients"].queryset = Recipient.objects.filter(
            owner=self.request.user
        )
        return form

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MailingUpdateView(LoginRequiredMixin, UpdateView):
    """Обновляет существующую рассылку.
    Ограничивает выбор сообщения и получателей только теми, что принадлежат пользователю.
    Доступ только владельцу или администратору.
    """

    model = Mailing
    form_class = MailingForm
    template_name = "mailservices/mailing_form.html"
    success_url = reverse_lazy("mailservices:mailing_list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["message"].queryset = Message.objects.filter(
            owner=self.request.user
        )
        form.fields["recipients"].queryset = Recipient.objects.filter(
            owner=self.request.user
        )
        return form


class MailingDeleteView(LoginRequiredMixin, DeleteView):
    """Удаляет рассылку после подтверждения.
    Доступ только владельцу или администратору.
    """

    model = Mailing
    template_name = "mailservices/mailing_confirm_delete.html"
    success_url = reverse_lazy("mailservices:mailing_list")


class MailingDetailView(DetailView):
    """Отображает детальную информацию о рассылке, включая связанное сообщение.
    Доступ только владельцу или администратору (если реализованы права).
    """

    model = Mailing
    context_object_name = "mailing"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["message"] = self.object.message
        return context


class MailingNowView(LoginRequiredMixin, View):
    """Запускает немедленную отправку рассылки по запросу пользователя.
    Доступна только владельцу рассылки. После отправки показывает уведомление.
    """

    def post(self, request, pk):
        mailing = get_object_or_404(Mailing, pk=pk)

        if mailing.owner != request.user:
            messages.error(request, "Вы не можете отправить чужую рассылку.")
            return redirect("mailservices:mailing_list")

        send_mailing(mailing)
        messages.success(request, f"Рассылка '{mailing}' была обработана.")
        return redirect("mailservices:mailing_list")


# === MailAttempt Views ===


class AttemptListView(LoginRequiredMixin, ListView):
    """Отображает историю попыток отправки писем.
    Администратор и модератор видят все попытки. Обычный пользователь — только свои.
    Поддерживает пагинацию (10 записей на страницу).
    """

    model = MailAttempt
    template_name = "mailservices/attempt_list.html"
    context_object_name = "attempts"
    paginate_by = 10

    def test_func(self):
        """Проверяет права доступа: админ, модератор или авторизованный пользователь."""
        user = self.request.user
        return (
            user.is_superuser
            or (hasattr(user, "is_moderator") and user.is_moderator)
            or user.is_authenticated
        )

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return MailAttempt.objects.all().select_related("mailing", "mailing__owner")

        if hasattr(user, "is_moderator") and user.is_moderator:
            return MailAttempt.objects.all().select_related("mailing", "mailing__owner")

        return MailAttempt.objects.filter(mailing__owner=user).select_related("mailing")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "История отправки писем"
        return context


# === просмотр информации пользователей группами Админа и Модератора ===


class UserRecipientListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    Отображает список получателей, принадлежащих указанному пользователю.
    Доступ имеют пользователи с правом 'mailservices.can_view_all_recipients'.
    Attributes:
        model (Model): Recipient.
        template_name (str): Шаблон 'mailservices/client_list.html'.
        context_object_name (str): Имя переменной в шаблоне — 'recipients'.
    URL параметр:
        user_id (int): ID пользователя, чьих получателей нужно отобразить.
    Context:
        owner (User): Пользователь, которому принадлежат получатели.
    """

    model = Recipient
    template_name = "mailservices/client_list.html"
    context_object_name = "recipients"  # теперь в шаблоне: {{ clients }}

    def test_func(self):
        """Разрешаем доступ, если есть право просмотра всех клиентов"""
        return self.request.user.has_perm("mailservices.can_view_all_recipients")

    def get_queryset(self):
        # Получаем ID пользователя из URL
        user_id = self.kwargs["user_id"]
        # Находим владельца
        self.owner = get_object_or_404(User, pk=user_id)
        # Возвращаем клиентов этого владельца
        return Recipient.objects.filter(owner=self.owner)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["owner"] = self.owner  # теперь self.owner определён
        return context


class UserMessageListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    Отображает список сообщений, принадлежащих указанному пользователю.
    Доступ имеют пользователи с правом 'mailservices.can_view_all_messages'.
    Attributes:
        model (Model): Message.
        template_name (str): Шаблон 'mailservices/message_list.html'.
        context_object_name (str): Имя переменной в шаблоне — 'messages'.
    URL параметр:
        user_id (int): ID пользователя, чьи сообщения нужно отобразить.
    Context:
        owner (User): Пользователь, которому принадлежат сообщения.
    """

    model = Message
    template_name = "mailservices/message_list.html"
    context_object_name = "messages"

    def test_func(self):
        return self.request.user.has_perm("mailservices.can_view_all_messages")

    def get_queryset(self):
        # Получаем ID пользователя из URL
        user_id = self.kwargs["user_id"]
        # Находим владельца
        self.owner = get_object_or_404(User, pk=user_id)
        # Возвращаем клиентов этого владельца
        return Message.objects.filter(owner=self.owner)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["owner"] = self.owner  # теперь self.owner определён
        return context


class UserMailingListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    Отображает список рассылок, принадлежащих указанному пользователю.
    Доступ имеют пользователи с правом 'mailservices.can_view_all_mailings'.
    Attributes:
        model (Model): Mailing.
        template_name (str): Шаблон 'mailservices/mailing_list.html'.
        context_object_name (str): Имя переменной в шаблоне — 'mailing'.
    URL параметр:
        user_id (int): ID пользователя, чьи рассылки нужно отобразить.
    Context:
        owner (User): Пользователь, которому принадлежат рассылки.
        now (datetime): Текущее время для отображения кнопок управления в шаблоне.
    """

    model = Mailing
    template_name = "mailservices/mailing_list.html"
    context_object_name = "mailing"

    def test_func(self):
        return self.request.user.has_perm("mailservices.can_view_all_mailings")

    def get_queryset(self):
        # Получаем ID пользователя из URL
        user_id = self.kwargs["user_id"]
        # Находим владельца
        self.owner = get_object_or_404(User, pk=user_id)
        # Возвращаем клиентов этого владельца
        return Mailing.objects.filter(owner=self.owner)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["owner"] = self.owner  # теперь self.owner определён
        context["now"] = (
            timezone.now()
        )  # Для корректного отображения кнопки "Отправить" в шаблоне по времени
        return context


@login_required
def toggle_user_block_mailing(request, pk):
    """Блокировка рассылки пользователя админом или модератором"""
    mailing = get_object_or_404(Mailing, pk=pk)

    # Переключаем статус
    mailing.status = "completed"
    mailing.save()

    return redirect("mailservices:mailing_list")
