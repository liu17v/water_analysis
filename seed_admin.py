"""创建默认管理员账号"""
import asyncio
from app.config.database import AsyncSessionMaker
from app.models import init_tables
from app.models.user import User
from app.utils.jwt_util import get_password_hash
from sqlalchemy import select


async def seed():
    await init_tables()
    async with AsyncSessionMaker() as db:
        result = await db.execute(select(User).where(User.username == "admin"))
        if result.scalar_one_or_none():
            print("管理员账号已存在，跳过")
            return
        user = User(username="admin", password_hash=get_password_hash("admin123"), role="admin")
        db.add(user)
        await db.commit()
        print("管理员账号创建成功: admin / admin123")


if __name__ == "__main__":
    asyncio.run(seed())
