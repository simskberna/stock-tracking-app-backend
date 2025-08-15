from typing import Optional, List
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User
from app.security import hash_password, verify_password

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session  # Burada self.session kullan

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(select(User).filter(User.email == email))
        return result.scalars().first()

    async def create(self, email: str, password: str, full_name: str) -> User:
        hashed_password = hash_password(password)
        new_user = User(email=email, hashed_password=hashed_password, full_name=full_name)
        self.session.add(new_user)
        await self.session.commit()
        return new_user

    async def authenticate(self, email: str, password: str) -> Optional[User]:
        user = await self.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.session.execute(select(User).filter(User.id == user_id))
        return result.scalars().first()

    async def get_all_users(self) -> List[User]:
        """Tüm kullanıcıları getir"""
        result = await self.session.execute(select(User))
        return result.scalars().all()

    async def get_all_user_emails(self) -> List[str]:
        """Tüm kullanıcıların email adreslerini getir"""
        result = await self.session.execute(select(User.email).where(User.email.isnot(None)))
        emails = result.scalars().all()
        return emails

    async def get_active_users(self) -> List[User]:
        """Aktif kullanıcıları getir (opsiyonel)"""
        result = await self.session.execute(select(User).filter(User.is_active == True))
        return result.scalars().all()
