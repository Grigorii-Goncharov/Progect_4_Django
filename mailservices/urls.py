# urls.py
from django.urls import path
from . import views
from .apps import MailsevicesConfig

app_name = MailsevicesConfig.name

urlpatterns = [
    path("", views.home_view, name="home"),
    # Recipient URLs
    path("recipients/", views.RecipientListView.as_view(), name="recipient_list"),
    path("recipients/create/", views.RecipientCreateView.as_view(), name="recipient_create"),
    path("recipients/<int:pk>/detail/", views.RecipientDetailView.as_view(), name="recipient_detail"),
    path("recipients/<int:pk>/edit/", views.RecipientUpdateView.as_view(), name="recipient_edit"),
    path("recipients/<int:pk>/delete/", views.RecipientDeleteView.as_view(), name="recipient_confirm_delete"),
    # Message URLs
    path("messages/", views.MessageListView.as_view(), name="message_list"),
    path("messages/create/", views.MessageCreateView.as_view(), name="message_create"),
    path("messages/<int:pk>/detail/", views.RecipientDetailView.as_view(), name="message_detail"),
    path("messages/<int:pk>/edit/", views.MessageUpdateView.as_view(), name="message_edit"),
    path("messages/<int:pk>/delete/", views.MessageDeleteView.as_view(), name="message_confirm_delete"),
    # Mailing URLs
    path("mailings/", views.MailingListView.as_view(), name="mailing_list"),
    path("mailings/create/", views.MailingCreateView.as_view(), name="mailing_create"),
    path("mailings/<int:pk>/detail/", views.MailingDetailView.as_view(), name="mailing_detail"),
    path("mailings/<int:pk>/edit/", views.MailingUpdateView.as_view(), name="mailing_edit"),
    path("mailings/<int:pk>/delete/", views.MailingDeleteView.as_view(), name="mailing_confirm_delete"),
]