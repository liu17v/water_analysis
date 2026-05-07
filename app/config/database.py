from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from .settings import get_settings

settings = get_settings()

engine = create_async_engine(settings.DATABASE_URL, pool_size=20, max_overflow=10, echo=False)

AsyncSessionMaker = async_sessionmaker(
    bind=engine, class_=AsyncSession,
    autoflush=False, autocommit=False, expire_on_commit=False,
)

Base = declarative_base()


async def get_db():
    db = AsyncSessionMaker()
    try:
        yield db
    finally:
        await db.close()
