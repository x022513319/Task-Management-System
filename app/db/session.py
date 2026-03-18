from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from ..core.config import settings

engine = create_async_engine(str(settings.SQLALCHEMY_DATABASE_URL))

AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    async with AsyncSessionFactory() as session:
        yield session
