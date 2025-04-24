from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete

from ..models.user import User
from ..schemas.user import UserCreate
from ..core.security import get_password_hash


def get_user_by_username(db: Session, username: str) -> User:
    """
    Get a user by username.
    Args:
        db (Session): database session.
        username (str): username of the user.
    Returns:
        User: user object.
    """
    stmt = select(User).where(User.username == username)
    return db.execute(stmt).scalars().first()


def get_user_by_id(db: Session, user_id: int) -> User:
    """
    Get a user by id.
    Args:
        db (Session): database session.
        user_id (int): id of the user.
    Returns:
        User: user object.
    """
    stmt = select(User).where(User.user_id == user_id)
    return db.execute(stmt).scalars().first()


def create_user(db: Session, user: UserCreate) -> User:
    '''Create user with hashed password.'''
    hashed_password = get_password_hash(user.password)

    db_user = User(
        username=user.username,
        name=user.name,
        password=hashed_password,
        phone=user.phone,
        email=user.email,
        address=user.address
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user
