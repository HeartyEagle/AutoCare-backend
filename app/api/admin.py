from fastapi import APIRouter, Depends, HTTPException, status
from ..db.connection import Database
from ..crud.user import UserService
from ..core.dependencies import *
from ..schemas.admin import *
from ..models import User

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=AdminUsersResponse)
def get_all_users(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get all users in the system (customers, staff, admins).
    Restricted to admin users only.
    Args:
        current_user (User): The currently authenticated user.
        user_service (UserService): Service for user-related operations.
    Returns:
        AdminUsersResponse: A dictionary containing a list of all users.
    """
    # Restrict access to admin users only
    if current_user.discriminator != "admin":
        return AdminUsersResponse(
            status="failure",
            message="Unauthorized: Only admin users can access this endpoint"
        )

    # Fetch all users
    users = user_service.get_all_users()
    if not users:
        return AdminUsersResponse(
            status="failure",
            message="No users found"
        )

    return AdminUsersResponse(
        status="success",
        message="Users retrieved successfully",
        users=[{
            "user_id": user.user_id,
            "name": user.name,
            "username": user.username,
            "discriminator": user.discriminator,
            "email": user.email,
            "phone": user.phone,
            "address": user.address
        } for user in users]
    )


@router.get("/staff", response_model=AdminStaffListResponse)
def get_all_staff(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get all staff members in the system.
    Restricted to admin users only.
    Args:
        current_user (User): The currently authenticated user.
        user_service (UserService): Service for user-related operations.
    Returns:
        AdminStaffListResponse: A dictionary containing a list of all staff members.
    """
    # Restrict access to admin users only
    if current_user.discriminator != "admin":
        return AdminStaffListResponse(
            status="failure",
            message="Unauthorized: Only admin users can access this endpoint"
        )

    # Fetch all staff members
    staff_members = user_service.get_all_staff()
    if not staff_members:
        return AdminStaffListResponse(
            status="failure",
            message="No staff members found"
        )

    return AdminStaffListResponse(
        status="success",
        message="Staff members retrieved successfully",
        staff=[{
            "staff_id": staff.user_id,
            "name": staff.name,
            "username": staff.username,
            "email": staff.email,
            "phone": staff.phone,
            "address": staff.address,
            "jobtype": staff.jobtype.value if staff.jobtype else None,
            "hourly_rate": staff.hourly_rate
        } for staff in staff_members]
    )


@router.get("/vehicles", response_model=AdminVehiclesResponse)
def get_all_vehicles(
    current_user: User = Depends(get_current_user),
    vehicle_service: VehicleService = Depends(get_vehicle_service)
):
    """
    Get all vehicles in the system.
    Restricted to admin users only.
    Args:
        current_user (User): The currently authenticated user.
        vehicle_service (VehicleService): Service for vehicle-related operations.
    Returns:
        AdminVehiclesResponse: A dictionary containing a list of all vehicles.
    """
    # Restrict access to admin users only
    if current_user.discriminator != "admin":
        return AdminVehiclesResponse(
            status="failure",
            message="Unauthorized: Only admin users can access this endpoint"
        )

    # Fetch all vehicles
    vehicles = vehicle_service.get_all_vehicles()
    if not vehicles:
        return AdminVehiclesResponse(
            status="failure",
            message="No vehicles found"
        )

    return AdminVehiclesResponse(
        status="success",
        message="Vehicles retrieved successfully",
        vehicles=[{
            "vehicle_id": vehicle.vehicle_id,
            "customer_id": vehicle.customer_id,
            "license_plate": vehicle.license_plate,
            "brand": vehicle.brand.value if vehicle.brand else None,
            "model": vehicle.model,
            "type": vehicle.type.value if vehicle.type else None,
            "color": vehicle.color.value if vehicle.color else None,
            "remarks": vehicle.remarks
        } for vehicle in vehicles]
    )


@router.get("/repair-orders", response_model=AdminRepairOrdersResponse)
def get_all_repair_orders(
    current_user: User = Depends(get_current_user),
    repair_order_service: RepairOrderService = Depends(
        get_repair_order_service)
):
    """
    Get all repair orders in the system.
    Restricted to admin users only.
    Args:
        current_user (User): The currently authenticated user.
        repair_order_service (RepairOrderService): Service for repair order operations.
    Returns:
        AdminRepairOrdersResponse: A dictionary containing a list of all repair orders.
    """
    # Restrict access to admin users only
    if current_user.discriminator != "admin":
        return AdminRepairOrdersResponse(
            status="failure",
            message="Unauthorized: Only admin users can access this endpoint"
        )

    # Fetch all repair orders
    repair_orders = repair_order_service.get_all_repair_orders()
    if not repair_orders:
        return AdminRepairOrdersResponse(
            status="failure",
            message="No repair orders found"
        )

    return AdminRepairOrdersResponse(
        status="success",
        message="Repair orders retrieved successfully",
        repair_orders=[{
            "order_id": order.order_id,
            "vehicle_id": order.vehicle_id,
            "customer_id": order.customer_id,
            "request_id": order.request_id,
            "required_staff_type": order.required_staff_type.value if order.required_staff_type else None,
            "status": order.status.value if order.status else None,
            "order_time": order.order_time,
            "finish_time": order.finish_time,
            "remarks": order.remarks
        } for order in repair_orders]
    )
