import logging
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


class MailNotificationSender(object):
    def __init__(self,
                 seohost_mail_username: str,
                 seohost_mail_password: str,
                 seohost_mail_smtp_server_host: str,
                 seohost_mail_smtp_server_port: str):
        self._seohost_mail_username = seohost_mail_username
        self._seohost_mail_password = seohost_mail_password
        self._seohost_mail_smtp_server_host = seohost_mail_smtp_server_host
        self._seohost_mail_smtp_server_port = seohost_mail_smtp_server_port

    def _create_mail_message(self, mail_message_to: str, message: dict):
        message_content_plain = f'Nowa wiadomość w portalu Librus!<br><br>' \
                                f'OD: {message.get("message_sent_from")}<br>' \
                                f'DATA: {message.get("message_time_sent")}<br>' \
                                f'TEMAT: {message.get("message_subject")}<br>' \
                                f'TREŚĆ: <br>' \
                                f'{message.get("message_content")}<br><br>' \
                                f'Z poważaniem<br>Twoja Powiadamiaczka, czyli AutoMaciatek<br><br>'

        ending = '</p></body></html>'
        message_content_html = f'<html><body><p>{message_content_plain}{ending}'

        message_to_send = MIMEMultipart("alternative")
        message_to_send['Subject'] = f'LIBRUS - nowa wiadomość od {message.get("message_sent_from")}'
        message_to_send['From'] = self._seohost_mail_username
        message_to_send['To'] = mail_message_to

        part1 = MIMEText(message_content_plain, "plain")
        part2 = MIMEText(message_content_html, "html")

        message_to_send.attach(part1)
        message_to_send.attach(part2)

        return message_to_send

    def _send_mail(self, mail_message_to, messages_to_send: list):
        with smtplib.SMTP(self._seohost_mail_smtp_server_host, int(self._seohost_mail_smtp_server_port)) as server:
            server.starttls()

            server.login(self._seohost_mail_username, self._seohost_mail_password)

            for message in messages_to_send:
                server.send_message(self._create_mail_message(mail_message_to, message))
                time.sleep(5)

            server.close()

    def send_notifications(self, mail_message_to: str, new_messages: list):
        self._send_mail(mail_message_to, new_messages)
