from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, DateTime

from ..models.repair import RepairRequest, RepairAssignment, RepairOrder, RepairStatus, StaffJobType, RepairLog, Material
from ..events.audit_log_events import log_audit_event, object_to_dict
from ..models.audit import OperationType


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
    await db.flush()  # Ensure the request is added to the session
    await log_audit_event(
        db=db,
        target=db_request,
        operation=OperationType.INSERT,
        new_data=object_to_dict(db_request),
        operated_by=customer_id)
    await db.commit()
    await db.refresh(db_request)
    return db_request


async def get_repair_request_by_id(db: AsyncSession, request_id: int) -> Optional[RepairRequest]:
    """
    Get a repair request by ID.
    Args:
        db (Session): Database session.
        request_id (int): ID of the repair request.
    Returns:
        RepairRequest: The repair request if found, otherwise None.
    """
    stmt = select(RepairRequest).where(RepairRequest.request_id == request_id)
    result = await db.execute(stmt)
    return result.scalars().first()


async def create_repair_assignment(order_id: int, staff_id: int, time_worked: Optional[float], db: AsyncSession) -> RepairAssignment:
    """
    Create a new repair assignment.
    Args:
        order_id (int): ID of the repair order.
        staff_id (int): ID of the staff member.
        time_worked (float): Time worked on the assignment.
        db (Session): Database session.
    Returns:
        RepairAssignment: The created repair assignment.
    """
    db_assignment = RepairAssignment(
        order_id=order_id,
        staff_id=staff_id,
        time_worked=time_worked
    )
    db.add(db_assignment)
    await db.flush()
    await log_audit_event(
        db=db,
        target=db_assignment,
        operation=OperationType.INSERT,
        new_data=object_to_dict(db_assignment),
        operated_by=None)
    await db.commit()
    await db.refresh(db_assignment)
    return db_assignment


async def get_repair_assignment_by_id(db: AsyncSession, order_id: int, staff_id: int) -> Optional[RepairAssignment]:
    """
    Get a repair assignment by order ID and staff ID.
    Args:
        db (Session): Database session.
        order_id (int): ID of the repair order.
        staff_id (int): ID of the staff member.
    Returns:
        RepairAssignment: The repair assignment if found, otherwise None.
    """
    stmt = select(RepairAssignment).where(
        RepairAssignment.order_id == order_id,
        RepairAssignment.staff_id == staff_id
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def create_repair_order(order_id: int, vehicle_id: int, customer_id: int, request_id: int, required_staff_type: StaffJobType,
                              status: RepairStatus, remarks: Optional[str], db: AsyncSession) -> RepairOrder:
    """
    Create a new repair order.
    Args:
        order_id (int): ID of the repair order.
        vehicle_id (int): ID of the vehicle.
        request_id (int): ID of the repair request.
        status (str): Status of the repair order.
        db (Session): Database session.
    Returns:
        RepairOrder: The created repair order.
    """
    db_order = RepairOrder(
        order_id=order_id,
        vehicle_id=vehicle_id,
        customer_id=customer_id,
        request_id=request_id,
        required_staff_type=required_staff_type,
        status=status,
        finish_time=None,
        remarks=remarks
    )
    db.add(db_order)
    await db.flush()  # Ensure the order is added to the session
    await log_audit_event(
        db=db,
        target=db_order,
        operation=OperationType.INSERT,
        new_data=object_to_dict(db_order),
        operated_by=None)
    await db.commit()
    await db.refresh(db_order)
    return db_order


async def get_repair_order_by_id(db: AsyncSession, order_id: int) -> Optional[RepairOrder]:
    """
    Get a repair order by ID.
    Args:
        db (Session): Database session.
        order_id (int): ID of the repair order.
    Returns:
        RepairOrder: The repair order if found, otherwise None.
    """
    stmt = select(RepairOrder).where(RepairOrder.order_id == order_id)
    result = await db.execute(stmt)
    return result.scalars().first()


async def update_repair_order_status(order_id: int, status: RepairStatus, operated_by: int, db: AsyncSession) -> RepairOrder:
    """
    Update the status of a repair order.
    Args:
        order_id (int): ID of the repair order.
        status (str): New status of the repair order.
        db (Session): Database session.
    Returns:
        RepairOrder: The updated repair order.
    """
    db_order = await get_repair_order_by_id(db, order_id)
    if db_order:
        old_data = object_to_dict(db_order)
        db_order.status = status
        await log_audit_event(
            db=db,
            target=db_order,
            operation=OperationType.UPDATE,
            old_data=old_data,
            new_data=object_to_dict(db_order),
            operated_by=None
        )
        await db.commit()
        await db.refresh(db_order)
    return db_order


async def update_repair_order_finish_time(order_id: int, finish_time: DateTime, db: AsyncSession) -> RepairOrder:
    """
    Update the finish time of a repair order.
    Args:
        order_id (int): ID of the repair order.
        finish_time (str): New finish time of the repair order.
        db (Session): Database session.
    Returns:
        RepairOrder: The updated repair order.
    """
    db_order = await get_repair_order_by_id(db, order_id)
    if db_order:
        old_data = object_to_dict(db_order)
        db_order.finish_time = finish_time
        await log_audit_event(
            db=db,
            target=db_order,
            operation=OperationType.UPDATE,
            old_data=old_data,
            new_data=object_to_dict(db_order),
            operated_by=None
        )
        await db.commit()
        await db.refresh(db_order)
    return db_order


async def delete_repair_order(order_id: int, operated_by: int, db: AsyncSession) -> Optional[RepairOrder]:
    """
    Delete a repair order by ID.
    Args:
        order_id (int): ID of the repair order.
        db (Session): Database session.
    Returns:
        RepairOrder: The deleted repair order if found, otherwise None.
    """
    db_order = await get_repair_order_by_id(db, order_id)
    if db_order:
        await log_audit_event(
            db=db,
            target=db_order,
            operation=OperationType.DELETE,
            old_data=object_to_dict(db_order),
            operated_by=operated_by
        )
        await db.delete(db_order)
        await db.commit()
    return db_order


async def create_repair_log(order_id: int, staff_id: int, log_message: str, db: AsyncSession) -> RepairLog:
    """
    Create a new repair log.
    Args:
        order_id (int): ID of the repair order.
        staff_id (int): ID of the staff member.
        description (str): Description of the repair log.
        material_fee (float): Material fee for the repair log.
        db (Session): Database session.
    Returns:
        RepairLog: The created repair log.
    """
    db_log = RepairLog(
        order_id=order_id,
        staff_id=staff_id,
        log_message=log_message
    )
    db.add(db_log)
    await db.flush()
    await log_audit_event(
        db=db,
        target=db_log,
        operation=OperationType.INSERT,
        new_data=object_to_dict(db_log),
        operated_by=staff_id)
    await db.commit()
    await db.refresh(db_log)
    return db_log


async def get_repair_log_by_id(log_id: int, db: AsyncSession) -> Optional[RepairLog]:
    """
    Get a repair log by ID.
    Args:
        log_id (int): ID of the repair log.
        db (AsyncSession): Database session.
    Returns:
        RepairLog: The repair log if found, otherwise None.
    """
    stmt = select(RepairLog).where(RepairLog.log_id == log_id)
    result = await db.execute(stmt)
    return result.scalars().first()


async def create_material(log_id: int, name: str, quantity: float, unit_price: float, remarks: Optional[str], db: AsyncSession) -> Material:
    """
    Create a new material entry for a repair log.
    Args:
        log_id (int): ID of the repair log.
        name (str): Name of the material.
        quantity (float): Quantity of the material used.
        unit_price (float): Unit price of the material.
        remarks (Optional[str]): Additional remarks about the material.
        db (AsyncSession): Database session.
    Returns:
        Material: The created material entry.
    """
    db_material = Material(
        log_id=log_id,
        name=name,
        quantity=quantity,
        unit_price=unit_price,
        remarks=remarks
    )
    db.add(db_material)
    await db.flush()
    await log_audit_event(
        db=db,
        target=db_material,
        operation=OperationType.INSERT,
        new_data=object_to_dict(db_material),
        operated_by=None)
    await db.commit()
    await db.refresh(db_material)
    return db_material
