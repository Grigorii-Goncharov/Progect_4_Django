from django.db import models

class Recipient(models.Model):
    email = models.EmailField(
        unique=True,
        verbose_name="Email",
        help_text="Уникальный адрес электронной почты получателя"
    )
    full_name = models.CharField(
        max_length=255,
        verbose_name="Ф. И. О.",
        help_text="Полное имя получателя"
    )
    comment = models.TextField(
        blank=True, null=True,
        verbose_name="Комментарий",
        help_text="Дополнительная информация о получателе"
    )

    class Meta:
        verbose_name = "Получатель рассылки"
        verbose_name_plural = "Получатели рассылки"

    def __str__(self):
        return f"{self.full_name} ({self.email})"

