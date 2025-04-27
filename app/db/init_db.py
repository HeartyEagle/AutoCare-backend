from .base import Base
from .session import engine

# Database initialization


async def init_db():
    '''Initialize the database'''
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
