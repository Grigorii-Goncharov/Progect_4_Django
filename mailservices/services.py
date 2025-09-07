from django.utils import timezone
from .models import MailAttempt
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_mailing(mailing):
    """Отправляет электронные письма всем получателям указанной рассылки.
    Функция выполняет следующие действия:
    1. Проверяет, не завершена ли уже рассылка — если да, выходит без действий.
    2. Проверяет, не наступило ли время окончания рассылки — если да, обновляет статус на 'completed' и выходит.
    3. Если статус 'created', меняет его на 'started'.
    4. Отправляет письмо каждому получателю из списка рассылки.
    5. Для каждой попытки отправки создаёт запись в модели MailAttempt с результатом (успех/ошибка).
    6. После отправки повторно проверяет, не наступило ли время окончания — если да, завершает рассылку.
    Логирование и консольный вывод используются для отслеживания хода выполнения и отладки.
    Args:
        mailing (Mailing): Экземпляр модели Mailing, содержащий настройки рассылки,
                         включая сообщение, получателей и временные рамки.
    Returns:
        None
    Raises:
        Любые исключения, возникающие при отправке писем, перехватываются и логируются,
        но не прерывают выполнение функции — вместо этого создаётся запись с ошибкой в MailAttempt.
        Отправит письма всем получателям, если время не истекло и рассылка не завершена.
    """
    print("*" * 40)
    print(f"   send_mailing вызвана для ID={mailing.pk}")
    print(f"   Текущий статус: {mailing.status}")
    print(f"   Время завершения рассылки: {mailing.end_datetime}")
    print(f"   Текущее время: {timezone.now()}")

    logger.info(f"=== НАЧАЛО ОТПРАВКИ РАССЫЛКИ ID={mailing.pk} ===")
    logger.info(f"Текущий статус: {mailing.status}")

    # 1. Уже завершена — выходим
    if mailing.status == "completed":
        logger.warning(f"Рассылка {mailing.pk} уже завершена. Выход.")
        print("  Уже завершена — выход.")
        return

    # 2. Проверка: время окончания уже прошло?
    now_before = timezone.now()
    end_dt = mailing.end_datetime

    logger.info(f"Текущее время (UTC): {now_before}")
    logger.info(f"Время окончания (UTC): {end_dt}")
    print(f"   Сравнение: {now_before} > {end_dt} → {now_before > end_dt}")

    if now_before > end_dt:
        print("  ВРЕМЯ ИСТЕКЛО — МЕНЯЕМ СТАТУС НА 'completed'")
        logger.warning(f"  Время окончания прошло. Завершаем рассылку {mailing.pk}.")

        mailing.status = "completed"
        mailing.save()  # Сохраняем в БД

        # Принудительно перечитываем из БД, чтобы убедиться
        mailing.refresh_from_db()
        print(f"  Статус после save(): {mailing.status} (должен быть 'completed')")

        logger.info("Статус изменён на 'completed' и сохранён.")
        return

    # 3. Если создана — меняем на "started"
    if mailing.status == "created":
        print("  Меняем статус с 'created' на 'started'")
        logger.info(f"Рассылка {mailing.pk} в статусе 'created'. Меняем на 'started'.")
        mailing.status = "started"
        mailing.save()
        logger.info("Статус изменён на 'started'.")

    # 4. Подготовка к отправке
    subject = mailing.message.mail_title
    body = mailing.message.mail_body
    from_email = settings.DEFAULT_FROM_EMAIL
    recipients = mailing.recipients.all()

    logger.info(f"Отправка писем: {recipients.count()} получателей")

    for i, client in enumerate(recipients):
        logger.info(f"[{i+1}/{recipients.count()}] Отправка на {client.email}")

        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=from_email,
                recipient_list=[client.email],
                fail_silently=False,  # Параметр для отлова ошибки отправления
            )
            status = "success"
            server_response = "Успешно отправлено"
            logger.info(f"  Письмо на {client.email} отправлено.")
        except Exception as e:
            status = "failed"
            server_response = str(e)
            logger.error(f"  Ошибка при отправке на {client.email}: {e}")

        # Заполняем попытку в модель
        MailAttempt.objects.create(
            status=status, server_response=server_response, mailing=mailing
        )

    # 5. Проверка времени ПОСЛЕ отправки
    now_after = timezone.now()
    logger.info(f"Отправка завершена. Текущее время: {now_after}")

    if now_after >= mailing.end_datetime:
        logger.warning(
            f"  Время окончания достигнуто. Завершаем рассылку {mailing.pk}."
        )
        if mailing.status != "completed":
            print("  Время истекло после отправки — завершаем.")
            mailing.status = "completed"
            mailing.save()

            # Достаем обновленные данные из БД
            mailing.refresh_from_db()
            print(f"  Статус после завершения: {mailing.status}")

            logger.info("Статус изменён на 'completed'.")
    else:
        logger.info("  Время окончания ещё не наступило.")

    logger.info(f"=== ЗАВЕРШЕНО: Рассылка ID={mailing.pk} ===\n")
    print("*" * 40)
