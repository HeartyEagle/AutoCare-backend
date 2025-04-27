from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from urllib.parse import quote

# Info of the database
DATABASE = "mysql+aiomysql"
USER = "macrohard"
PASSWORD = quote("M@cr0h@rd!2025$")
HOST = "localhost"
PORT = "3308"
DB_NAME = "autocare_db"

# Create the database URL
SQLALCHEMY_DATABASE_URL = f"{DATABASE}://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"

engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True, future=True)

# Create the database session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession
)


async def get_db():
    '''Get a database session.'''
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()
