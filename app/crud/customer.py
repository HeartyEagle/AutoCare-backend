from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.customer import Vehicle, VehicleBrand, VehicleType, VehicleColor, Feedback
from ..events.audit_log_events import log_audit_event, object_to_dict
from ..models.audit import OperationType


async def create_vehicle(
        customer_id: int, license_plate: str, brand: VehicleBrand, model: str,
        type: VehicleType, color: VehicleColor, remarks: Optional[str], operated_by: int, db: AsyncSession) -> Vehicle:
    """
    Create a new vehicle for a customer.
    Args:
        customer_id (int): ID of the customer.
        license_plate (str): License plate of the vehicle.
        brand (str): Brand of the vehicle.
        model (str): Model of the vehicle.
        type (str): Type of the vehicle.
        db (Session): Database session.
    Returns:
        Vehicle: The created vehicle.
    """
    db_vehicle = Vehicle(
        customer_id=customer_id,
        license_plate=license_plate,
        brand=brand,
        model=model,
        type=type,
        color=color,
        remarks=remarks
    )
    db.add(db_vehicle)
    await db.flush()
    await log_audit_event(
        db=db,
        target=db_vehicle,
        operation=OperationType.INSERT,
        new_data=object_to_dict(db_vehicle),
        operated_by=operated_by
    )
    await db.commit()
    await db.refresh(db_vehicle)
    return db_vehicle


async def get_vehicle_by_id(db: AsyncSession, vehicle_id: int) -> Vehicle | None:
    """
    Get a vehicle by ID asynchronously.
    Args:
        db (AsyncSession): Asynchronous database session.
        vehicle_id (int): ID of the vehicle.
    Returns:
        Vehicle | None: Vehicle object if found, otherwise None.
    """
    stmt = select(Vehicle).where(Vehicle.vehicle_id == vehicle_id)
    result = await db.execute(stmt)
    return result.scalars().first()


async def create_feedback(
        customer_id: int, log_id: int, rating: int, comments: Optional[str], operated_by: int, db: AsyncSession) -> Feedback:
    """
    Create a new feedback for a repair log.
    Args:
        customer_id (int): ID of the customer.
        log_id (int): ID of the repair log.
        rating (int): Rating given by the customer.
        comments (str): Comments provided by the customer.
        db (Session): Database session.
    Returns:
        Feedback: The created feedback.
    """
    db_feedback = Feedback(
        customer_id=customer_id,
        log_id=log_id,
        rating=rating,
        comments=comments
    )
    db.add(db_feedback)
    await db.flush()
    await log_audit_event(
        db=db,
        target=db_feedback,
        operation=OperationType.INSERT,
        new_data=object_to_dict(db_feedback),
        operated_by=operated_by
    )
    await db.commit()
    await db.refresh(db_feedback)
    return db_feedback


async def get_feedback_by_id(db: AsyncSession, feedback_id: int) -> Feedback | None:
    """
    Get a feedback by ID asynchronously.
    Args:
        db (AsyncSession): Asynchronous database session.
        feedback_id (int): ID of the feedback.
    Returns:
        Feedback | None: Feedback object if found, otherwise None.
    """
    stmt = select(Feedback).where(Feedback.feedback_id == feedback_id)
    result = await db.execute(stmt)
    return result.scalars().first()
