from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User
from app.security import hash_password, verify_password

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str):
        result = await self.session.execute(select(User).filter(User.email == email))
        return result.scalars().first()

    async def create(self, email: str, password: str, full_name: str):
        hashed_password = hash_password(password)
        new_user = User(email=email, hashed_password=hashed_password, full_name=full_name)
        self.session.add(new_user)
        await self.session.commit()

        return new_user

    async def authenticate(self, email: str, password: str):
        user = await self.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
