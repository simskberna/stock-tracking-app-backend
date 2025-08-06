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

    async def create(self, email: str, password: str):
        hashed_pw = hash_password(password)
        user = User(email=email, hashed_password=hashed_pw)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def authenticate(self, email: str, password: str):
        user = await self.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
