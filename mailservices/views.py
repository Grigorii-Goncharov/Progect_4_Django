# views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy

from .forms import RecipientForm, MessageForm, MailingForm
from .models import Mailing, Recipient, Message


# Главная страница — отображение статистики
# @login_required
def home_view(request):
    """ Отображение главное страницы количество всех рассылок, количество активных рассылок (со статусом
    'Запущена') и количество уникальных получателей.
    """
    total_mailings = Mailing.objects.filter(owner=request.user).count()
    active_mailings = Mailing.objects.filter(owner=request.user, status="started").count()
    unique_recipients = Recipient.objects.filter(owner=request.user).values('email').distinct().count()

    context = {
        "total_mailings": total_mailings,
        "active_mailings": active_mailings,
        "unique_recipients": unique_recipients,
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
        return Mailing.objects.filter(owner=self.request.user).select_related("message")


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
