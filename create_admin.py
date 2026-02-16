
import asyncio
from database import engine, Base
from models import User
from auth import get_password_hash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

async def create_admin():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as db:
        result = await db.execute(select(User).where(User.username == "admin"))
        user = result.scalars().first()
        
        if not user:
            print("Creating admin user...")
            hashed_pw = get_password_hash("admin123")
            new_user = User(username="admin", hashed_password=hashed_pw, role="admin")
            db.add(new_user)
            await db.commit()
            print("Admin user created. Username: 'admin', Password: 'admin123'")
        else:
            print("Admin user already exists.")

if __name__ == "__main__":
    asyncio.run(create_admin())
