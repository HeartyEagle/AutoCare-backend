from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.user import User, Admin, Staff, Customer
from ..schemas.user import UserCreate, StaffCreate
from ..core.security import get_password_hash


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    """
    Get a user by username asynchronously.
    Args:
        db (AsyncSession): Asynchronous database session.
        username (str): Username of the user.
    Returns:
        User | None: User object if found, otherwise None.
    """
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    return result.scalars().first()


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    """
    Get a user by ID asynchronously.
    Args:
        db (AsyncSession): Asynchronous database session.
        user_id (int): ID of the user.
    Returns:
        User | None: User object if found, otherwise None.
    """
    stmt = select(User).where(User.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalars().first()


async def create_customer(db: AsyncSession, user: UserCreate) -> Customer:
    """
    Create a customer with a hashed password asynchronously.
    Args:
        db (AsyncSession): Asynchronous database session.
        user (UserCreate): User creation schema with user details.
    Returns:
        Customer: Created customer object.
    """
    hashed_password = get_password_hash(user.password)
    db_user = Customer(
        username=user.username,
        name=user.name,
        password=hashed_password,
        phone=user.phone,
        email=user.email,
        address=user.address
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def create_admin(db: AsyncSession, user: UserCreate) -> Admin:
    """
    Create an admin with a hashed password asynchronously.
    Args:
        db (AsyncSession): Asynchronous database session.
        user (UserCreate): User creation schema with user details.
    Returns:
        Admin: Created admin object.
    """
    hashed_password = get_password_hash(user.password)
    db_user = Admin(
        username=user.username,
        name=user.name,
        password=hashed_password,
        phone=user.phone,
        email=user.email,
        address=user.address,
        discriminator="admin"
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def create_staff(db: AsyncSession, user: StaffCreate) -> Staff:
    """
    Create a staff member with a hashed password asynchronously.
    Args:
        db (AsyncSession): Asynchronous database session.
        user (StaffCreate): User creation schema with user details.
    Returns:
        Staff: Created staff object.
    """
    hashed_password = get_password_hash(user.password)
    db_user = Staff(
        username=user.username,
        name=user.name,
        password=hashed_password,
        phone=user.phone,
        email=user.email,
        address=user.address,
        discriminator="staff",
        jobtype=user.jobtype,
        hourly_rate=user.hourly_rate
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def update_user_info(user_id: int, name: str, email: str, address: str, phone: str, db: AsyncSession) -> User | None:
    """
    Update user information asynchronously.
    Args:
        user_id (int): ID of the user to update.
        name (str): New name of the user.
        email (str): New email of the user.
        address (str): New address of the user.
        phone (str): New phone number of the user.
        db (AsyncSession): Asynchronous database session.
    Returns:
        User | None: Updated user object if found, otherwise None.
    """
    db_user = await get_user_by_id(db, user_id)
    if db_user:
        db_user.name = name
        db_user.email = email
        db_user.address = address
        db_user.phone = phone
        await db.commit()
        await db.refresh(db_user)
    return db_user
