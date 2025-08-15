import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
import asyncio
import logging
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import time

logger = logging.getLogger(__name__)
from dotenv import load_dotenv
load_dotenv()

@dataclass
class GmailConfig:
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    username: str = os.getenv("EMAIL_USERNAME")
    password: str = os.getenv("EMAIL_PASSWORD")  # App Password buraya
    from_email: str = os.getenv("FROM_EMAIL")
    from_name: str = os.getenv("FROM_NAME")


class GmailEmailService:
    def __init__(self, config: GmailConfig):
        self.config = config
        if not all([self.config.username, self.config.password, self.config.from_email]):
            logger.error("Gmail configuration is incomplete. Check environment variables.")

    async def send_email(self, to_email: str, subject: str, body: str, is_html: bool = True):
        """Tekil email gönderme"""
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._send_email_sync,
                to_email,
                subject,
                body,
                is_html
            )
            logger.info(f"Email sent successfully to {to_email}")
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")

    async def send_bulk_email(self, recipients: List[str], subject: str, body: str, is_html: bool = True):
        """Toplu email gönderme (Gmail rate limiting'e uygun)"""
        if not recipients:
            logger.warning("No recipients provided for bulk email")
            return

        # Gmail günlük limit: 500 email, saniyede 10-15 email önerilen
        batch_size = 10
        delay_between_batches = 2  # saniye

        try:
            for i in range(0, len(recipients), batch_size):
                batch = recipients[i:i + batch_size]
                tasks = []

                for email in batch:
                    task = self.send_email(email, subject, body, is_html)
                    tasks.append(task)

                # Batch'i gönder
                await asyncio.gather(*tasks, return_exceptions=True)
                logger.info(f"Sent batch {i // batch_size + 1}: {len(batch)} emails")

                # Rate limiting için bekle
                if i + batch_size < len(recipients):
                    await asyncio.sleep(delay_between_batches)

            logger.info(f"Bulk email completed: {len(recipients)} recipients")

        except Exception as e:
            logger.error(f"Failed to send bulk email: {e}")

    def _send_email_sync(self, to_email: str, subject: str, body: str, is_html: bool = True):
        """Senkron email gönderme"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.config.from_name} <{self.config.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject

            # HTML ve plain text versiyonlarını ekle
            if is_html:
                # Plain text version (HTML'den basitçe oluştur)
                plain_text = self._html_to_plain(body)
                msg.attach(MIMEText(plain_text, 'plain'))
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))

            # Gmail SMTP ile gönder
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.username, self.config.password)
                server.send_message(msg)

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"Gmail authentication failed. Check your app password: {e}")
            raise Exception("Gmail authentication failed. Please verify your app password.")
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}")
            raise

    def _html_to_plain(self, html_content: str) -> str:
        """HTML'den plain text oluştur"""
        import re
        # HTML taglerini kaldır
        text = re.sub('<[^<]+?>', '', html_content)
        # Entities'leri değiştir
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        # Fazla boşlukları temizle
        text = re.sub(r'\s+', ' ', text).strip()
        return text


# Global Gmail service
gmail_config = GmailConfig()
gmail_email_service = GmailEmailService(gmail_config)