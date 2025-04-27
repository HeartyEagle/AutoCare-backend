from sqlalchemy.orm import Session
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.repair import RepairRequest
from ..models.customer import Vehicle, VehicleBrand, VehicleType, VehicleColor


async def create_repair_request(vehicle_id: int, customer_id: int, description: str, db: AsyncSession) -> RepairRequest:
    """
    Create a new repair request.
    Args:
        vehicle_id (int): ID of the vehicle.
        customer_id (int): ID of the customer.
        description (str): Description of the repair request.
        db (Session): Database session.
    Returns:
        RepairRequest: The created repair request.
    """
    db_request = RepairRequest(
        vehicle_id=vehicle_id,
        customer_id=customer_id,
        description=description
    )
    db.add(db_request)
    await db.commit()
    await db.refresh(db_request)
    return db_request


async def create_vehicle(
        customer_id: int, license_plate: str, brand: VehicleBrand, model: str,
        type: VehicleType, color: VehicleColor, remarks: Optional[str], db: AsyncSession) -> Vehicle:
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
    await db.commit()
    await db.refresh(db_vehicle)
    return db_vehicle
