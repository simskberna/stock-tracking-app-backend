from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import UserRepository
from app.services.email_service import gmail_email_service
from app.routers.ws import manager
from app.database import AsyncSessionLocal
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self):
        pass

    async def get_all_user_emails(self) -> List[str]:
        """Database'deki tüm kullanıcıların email'lerini getir"""
        async with AsyncSessionLocal() as db:
            user_repo = UserRepository(db)
            users = await user_repo.get_all_users()
            return [user.email for user in users if user.email]

    async def send_notification_to_all_users(
            self,
            ws_message: dict,
            email_subject: str,
            email_body: str,
            send_email: bool = True
    ):
        """Tüm kullanıcılara hem WebSocket hem email bildirimi gönder"""

        # WebSocket bildirimi (sadece online kullanıcılara)
        if manager.active_connections:
            await manager.broadcast(ws_message)
            logger.info(f"WebSocket notification sent to {len(manager.active_connections)} active users")

        # Email bildirimi (Gmail SMTP ile tüm kullanıcılara)
        if send_email:
            try:
                all_emails = await self.get_all_user_emails()
                if all_emails:
                    await gmail_email_service.send_bulk_email(
                        recipients=all_emails,
                        subject=email_subject,
                        body=email_body,
                        is_html=True
                    )
                    logger.info(f"Gmail email notification sent to {len(all_emails)} users")
                else:
                    logger.warning("No users found in database")
            except Exception as e:
                logger.error(f"Failed to send email notifications: {e}")


# Global notification service
notification_service = NotificationService()