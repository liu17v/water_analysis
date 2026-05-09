"""数据库初始化：自动建库 + 建表 + Milvus 集合"""
import asyncio
from urllib.parse import urlparse, urlunparse
from sqlalchemy import create_engine, text
from app.models import init_tables
from app.services.milvus_service import connect, init_collection
from app.config.settings import get_settings
from app.config.logging import setup_logging, get_logger

setup_logging()
logger = get_logger("system")
settings = get_settings()


def _ensure_mysql_database():
    """连接 MySQL 服务端（不指定库），自动创建数据库（如不存在）"""
    # 从 DATABASE_URL 提取连接信息，构建无库名的同步连接串
    parsed = urlparse(settings.DATABASE_URL)
    db_name = parsed.path.lstrip("/")
    sync_url = urlunparse((
        "mysql+pymysql",
        f"{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port or 3306}",
        "/", "", "", ""
    )) + "?charset=utf8mb4"

    engine = create_engine(sync_url, echo=False)
    with engine.connect() as conn:
        conn.execute(text(
            f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
            f"DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        ))
        conn.commit()
    engine.dispose()
    logger.info(f"MySQL 数据库 [{db_name}] 已就绪")


async def seed():
    from app.config.database import AsyncSessionMaker
    from app.models.user import User
    from app.utils.jwt_util import get_password_hash

    async with AsyncSessionMaker() as db:
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.username == "admin"))
        if not result.scalar_one_or_none():
            db.add(User(
                username="admin",
                password_hash=get_password_hash("admin123"),
                role="admin",
            ))
            await db.commit()
            logger.info("默认管理员用户已创建 (admin / admin123)")


async def main():
    logger.info("========== 数据库初始化开始 ==========")

    # 1. 建库
    _ensure_mysql_database()

    # 2. 建表
    await init_tables()
    logger.info("MySQL 表结构创建完成")

    # 3. 种子数据
    try:
        await seed()
    except Exception as e:
        logger.warning(f"种子数据写入失败（可能表已存在）: {e}")

    # 4. Milvus 集合
    try:
        connect()
        init_collection()
        logger.info("Milvus 集合创建完成")
    except Exception as e:
        logger.warning(f"Milvus 初始化失败（可能未部署）: {e}")

    logger.info("========== 初始化完成 ==========")


if __name__ == "__main__":
    asyncio.run(main())
