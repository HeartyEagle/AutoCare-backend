from .base import Base
from .session import engine

# Database initialization


async def init_db():
    '''Initialize the database'''
    with engine.begin() as conn:
        conn.run_sync(Base.metadata.create_all)
