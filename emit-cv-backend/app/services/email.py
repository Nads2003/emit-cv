"""Envoi d'e-mails : SMTP en production ; « console » (journal + boîte d'envoi en mémoire) en développement et en test."""
import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

log = logging.getLogger("emit.email")
OUTBOX: list[dict] = []  # utilisé par les tests (backend console uniquement)


def envoyer(destinataire: str, sujet: str, corps: str) -> None:
    if settings.email_backend == "smtp":
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = settings.email_from, destinataire, sujet
        msg.set_content(corps)
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as s:
            if settings.smtp_starttls:
                s.starttls()
            if settings.smtp_user:
                s.login(settings.smtp_user, settings.smtp_password)
            s.send_message(msg)
        return
    OUTBOX.append({"to": destinataire, "subject": sujet, "body": corps})
    del OUTBOX[:-200]
    log.info("[E-MAIL console] à=%s sujet=%s\n%s", destinataire, sujet, corps)
