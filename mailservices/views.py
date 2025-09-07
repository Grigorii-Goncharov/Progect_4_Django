# views.py
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy

from .forms import RecipientForm, MessageForm, MailingForm
from .models import Mailing, Recipient, Message, MailAttempt
from .services import send_mailing


def home_view(request):
    # Общая статистика (видна всем)
    total_mailings = Mailing.objects.count()
    unique_recipients = Recipient.objects.count()

    # Активные рассылки: started или created (тоже общая или по владельцу)
    active_mailings = Mailing.objects.filter(
        status__in=['created', 'started']
    ).count()

    # Если пользователь авторизован — показываем его статистику
    if request.user.is_authenticated:
        my_total = Mailing.objects.filter(owner=request.user).count()
        my_active = Mailing.objects.filter(
            owner=request.user,
            status__in=['created', 'started']
        ).count()
    else:
        my_total = 0
        my_active = 0

    context = {
        "total_mailings": total_mailings,
        "active_mailings": active_mailings,
        "unique_recipients": unique_recipients,

        # Опционально: свои показатели
        'my_total': my_total,
        'my_active': my_active,
    }
    return render(request, "mailservices/home.html", context)



# Recipient CRUD
class RecipientListView(LoginRequiredMixin, ListView):

    model = Recipient
    template_name = "mailservices/recipient_list.html"
    context_object_name = "recipients"

    def get_queryset(self):
        return Recipient.objects.filter(owner=self.request.user)


class RecipientCreateView(LoginRequiredMixin, CreateView):
    """Внесение записи клиента"""
    model = Recipient
    form_class = RecipientForm
    template_name = "mailservices/recipient_form.html"
    success_url = reverse_lazy("mailservices:recipient_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

class RecipientDetailView(LoginRequiredMixin, DetailView):
    """Просмотр записи о клиенте"""
    model = Recipient
    context_object_name = "recipient"
    # pk_url_kwarg = "pk"


class RecipientUpdateView(LoginRequiredMixin, UpdateView):
    """Обновление записи клиента"""
    model = Recipient
    fields = ["email", "full_name", "comment"]
    template_name = "mailservices/recipient_form.html"
    success_url = reverse_lazy("mailservices:recipient_list")


class RecipientListView(LoginRequiredMixin, ListView):
    """Просмотр всех записей клиентов"""
    model = Recipient
    template_name = "mailservices/recipient_list.html"
    context_object_name = "recipients"

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Recipient.objects.all()  # Админ видит всех
        return Recipient.objects.filter(owner=self.request.user)  # Обычный пользователь — только свои


class RecipientDeleteView(LoginRequiredMixin, DeleteView):
    """просмотр записи клиента"""
    model = Recipient
    template_name = "mailservices/recipient_confirm_delete.html"
    success_url = reverse_lazy("mailservices:recipient_list")


# Message CRUD
class MessageListView(LoginRequiredMixin, ListView):
    """просмотр всех сообщений"""
    model = Message
    template_name = "mailservices/message_list.html"
    context_object_name = "messages"

    # def get_queryset(self):
    #     return Message.objects.filter(owner=self.request.user)

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Message.objects.all()  # Админ видит всех
        return Message.objects.filter(owner=self.request.user)  # Обычный пользователь — только свои


class MessageCreateView(LoginRequiredMixin, CreateView):
    """Создание сообщения"""
    model = Message
    form_class = MessageForm
    template_name = "mailservices/message_form.html"
    success_url = reverse_lazy("mailservices:message_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MessageUpdateView(LoginRequiredMixin, UpdateView):
    """Обновление сообщения рассылки"""
    model = Message
    form_class = MessageForm
    template_name = "mailservices/message_form.html"
    success_url = reverse_lazy("mailservices:message_list")


class MessageDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление сообщения рассылки"""
    model = Message
    template_name = "mailservices/message_confirm_delete.html"
    success_url = reverse_lazy("mailservices:message_list")


class MessageDetailView(LoginRequiredMixin, DetailView):
    """Просмотр Сообщения для рассылки"""
    model = Message
    context_object_name = "message"


# Mailing CRUD
class MailingListView(LoginRequiredMixin, ListView):
    """Просмотр списка рассылок"""
    model = Mailing
    template_name = "mailservices/mailing_list.html"
    context_object_name = "mailings"

    def get_queryset(self):
        # находим запись и если она есть  по времени завершения — автоматически завершаем просроченные рассылки
        now = timezone.now()
        Mailing.objects.filter(
            owner=self.request.user,
            status='started',
            end_datetime__lt=now
        ).update(status='completed')

        return Mailing.objects.filter(owner=self.request.user).select_related("message")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['now'] = timezone.now()
        return context


class MailingCreateView(LoginRequiredMixin, CreateView):
    """Создание рассылки"""
    model = Mailing
    form_class = MailingForm
    template_name = "mailservices/mailing_form.html"
    success_url = reverse_lazy("mailservices:mailing_list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Ограничиваем выбор только объектами пользователя
        form.fields["message"].queryset = Message.objects.filter(owner=self.request.user)
        form.fields["recipients"].queryset = Recipient.objects.filter(owner=self.request.user)
        return form

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MailingUpdateView(LoginRequiredMixin, UpdateView):
    """обновление рассылки"""
    model = Mailing
    form_class = MailingForm
    template_name = "mailservices/mailing_form.html"
    success_url = reverse_lazy("mailservices:mailing_list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["message"].queryset = Message.objects.filter(owner=self.request.user)
        form.fields["recipients"].queryset = Recipient.objects.filter(owner=self.request.user)
        return form


class MailingDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление рассылки"""
    model = Mailing
    template_name = "mailservices/mailing_confirm_delete.html"
    success_url = reverse_lazy("mailservices:mailing_list")


class MailingDetailView(DetailView):
    """Просмотр рассылки"""
    model = Mailing
    context_object_name = "mailing"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['message'] = self.object.message
        return context


class MailingNowView(LoginRequiredMixin, View):
    """
    Вьюха для ручной отправки рассылки по кнопке.
    Доступна только владельцу.
    """

    def post(self, request, pk):
        mail_send = get_object_or_404(Mailing, pk=pk)

        # Проверка владельца
        if  mail_send.owner != request.user:
            messages.error(request, "Вы не можете отправить чужую рассылку.")
            return redirect('mailservices:mailing_list')

        # Запускаем отправку
        send_mailing(mail_send)

        messages.success(request, f"Рассылка '{mail_send}' была обработана.")
        return redirect('mailservices:mailing_list')


class AttemptListView(LoginRequiredMixin, ListView):
    model = MailAttempt
    template_name = 'mailservices/attempt_list.html'
    context_object_name = 'attempts'
    paginate_by = 10

    def test_func(self):
        """Разрешаем: админ, модератор, владелец"""
        user = self.request.user
        return user.is_superuser or hasattr(user, 'is_moderator') and user.is_moderator or user.is_authenticated

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return MailAttempt.objects.all().select_related('mailing', 'mailing__owner')

        if hasattr(user, 'is_moderator') and user.is_moderator:
            return MailAttempt.objects.all().select_related('mailing', 'mailing__owner')

        # Обычный пользователь — только свои попытки
        return MailAttempt.objects.filter(mailing__owner=user).select_related('mailing')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'История отправки писем'
        return context
