import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
import json
import requests

class AlertManager:
    ALERT_LEVELS = {
        'INFO': 0,
        'WARNING': 1,
        'ERROR': 2,
        'CRITICAL': 3
    }

    @staticmethod
    def send_email_alert(subject, message, recipients=None):
        """
        Отправляет уведомление по электронной почте
        """
        if recipients is None:
            recipients = [admin[1] for admin in settings.ADMINS]

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                recipients,
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Failed to send email alert: {str(e)}")
            return False

    @staticmethod
    def send_slack_alert(message, channel=None, level='INFO'):
        """
        Отправляет уведомление в Slack
        """
        if not hasattr(settings, 'SLACK_WEBHOOK_URL'):
            return False

        if channel is None:
            channel = settings.DEFAULT_SLACK_CHANNEL

        try:
            payload = {
                'channel': channel,
                'username': 'Tracker Alert Bot',
                'text': message,
                'icon_emoji': AlertManager._get_emoji_for_level(level)
            }

            response = requests.post(
                settings.SLACK_WEBHOOK_URL,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'}
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to send Slack alert: {str(e)}")
            return False

    @staticmethod
    def _get_emoji_for_level(level):
        """
        Возвращает эмодзи в зависимости от уровня важности
        """
        emoji_map = {
            'INFO': ':information_source:',
            'WARNING': ':warning:',
            'ERROR': ':x:',
            'CRITICAL': ':rotating_light:'
        }
        return emoji_map.get(level.upper(), ':information_source:')

    @classmethod
    def alert(cls, message, level='INFO', channels=None):
        """
        Отправляет уведомление по всем доступным каналам
        """
        if channels is None:
            channels = ['email', 'slack']

        alert_sent = False

        if 'email' in channels:
            subject = f"[{level}] Tracker Alert"
            email_sent = cls.send_email_alert(subject, message)
            alert_sent = alert_sent or email_sent

        if 'slack' in channels:
            slack_sent = cls.send_slack_alert(message, level=level)
            alert_sent = alert_sent or slack_sent

        return alert_sent

    @classmethod
    def performance_alert(cls, view_name, response_time, threshold):
        """
        Отправляет уведомление о проблемах с производительностью
        """
        message = (
            f"Performance Alert: {view_name}\n"
            f"Response time: {response_time:.2f}s\n"
            f"Threshold: {threshold:.2f}s"
        )
        return cls.alert(message, level='WARNING')

    @classmethod
    def error_alert(cls, error_type, error_message, details=None):
        """
        Отправляет уведомление об ошибке
        """
        message = (
            f"Error Alert: {error_type}\n"
            f"Message: {error_message}\n"
        )
        if details:
            message += f"Details: {json.dumps(details, indent=2)}"
        return cls.alert(message, level='ERROR')

    @classmethod
    def security_alert(cls, event_type, details):
        """
        Отправляет уведомление о проблемах безопасности
        """
        message = (
            f"Security Alert: {event_type}\n"
            f"Details: {json.dumps(details, indent=2)}"
        )
        return cls.alert(message, level='CRITICAL', channels=['email', 'slack']) 