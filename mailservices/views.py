# views.py
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy

from .forms import RecipientForm, MessageForm, MailingForm
from .models import Mailing, Recipient, Message
from .services import send_mailing


# Главная страница — отображение статистики
# @login_required
# def home_view(request):
#     """ Отображение главное страницы количество всех рассылок, количество активных рассылок (со статусом
#     'Запущена') и количество уникальных получателей.
#     """
#     total_mailings = Mailing.objects.filter(owner=request.user).count()
#     active_mailings = Mailing.objects.filter(owner=request.user, status="started").count()
#     unique_recipients = Recipient.objects.filter(owner=request.user).values('email').distinct().count()
#
#     context = {
#         "total_mailings": total_mailings,
#         "active_mailings": active_mailings,
#         "unique_recipients": unique_recipients,
#     }
#     return render(request, "mailservices/home.html", context)


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
class RecipientListView(ListView):

    model = Recipient
    template_name = "mailservices/recipient_list.html"
    context_object_name = "recipients"

    def get_queryset(self):
        return Recipient.objects.filter(owner=self.request.user)


class RecipientCreateView(CreateView):
    """Внесение записи клиента"""
    model = Recipient
    form_class = RecipientForm
    template_name = "mailservices/recipient_form.html"
    success_url = reverse_lazy("mailservices:recipient_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

class RecipientDetailView(DetailView):
    """Просмотр записи о клиенте"""
    model = Recipient
    context_object_name = "recipient"
    # pk_url_kwarg = "pk"


class RecipientUpdateView(UpdateView):
    """Обновление записи клиента"""
    model = Recipient
    fields = ["email", "full_name", "comment"]
    template_name = "mailservices/recipient_form.html"
    success_url = reverse_lazy("mailservices:recipient_list")


class RecipientlistView(ListView):
    """Просмотр списка клиентов"""
    model = Recipient
    context_object_name = "products"
    template_name = "mailservices/home.html"


class RecipientDeleteView(DeleteView):
    """просмотр записи клиента"""
    model = Recipient
    template_name = "mailservices/recipient_confirm_delete.html"
    success_url = reverse_lazy("mailservices:recipient_list")


# Message CRUD
class MessageListView(ListView):
    """просмотр всех сообщений"""
    model = Message
    template_name = "mailservices/message_list.html"
    context_object_name = "messages"

    def get_queryset(self):
        return Message.objects.filter(owner=self.request.user)


class MessageCreateView(CreateView):
    """Создание сообщения"""
    model = Message
    form_class = MessageForm
    template_name = "mailservices/message_form.html"
    success_url = reverse_lazy("mailservices:message_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MessageUpdateView(UpdateView):
    """Обновление сообщения рассылки"""
    model = Message
    form_class = MessageForm
    template_name = "mailservices/message_form.html"
    success_url = reverse_lazy("mailservices:message_list")


class MessageDeleteView(DeleteView):
    """Удаление сообщения рассылки"""
    model = Message
    template_name = "mailservices/message_confirm_delete.html"
    success_url = reverse_lazy("mailservices:message_list")


class MessageDetailView(DetailView):
    """Просмотр Сообщения для рассылки"""
    model = Message
    context_object_name = "message"


# Mailing CRUD
class MailingListView(ListView):
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


class MailingCreateView(CreateView):
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


class MailingUpdateView(UpdateView):
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


class MailingDeleteView(DeleteView):
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


class MailingNowView(View):
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


