# api/staff.py
from fastapi import APIRouter, Depends, HTTPException, status
from ..db.connection import Database
from ..crud.user import UserService
from ..core.dependencies import *
from ..schemas.staff import *
from ..models import User

router = APIRouter(prefix="/staff", tags=["staff"])


@router.get("/{staff_id}/profile", response_model=StaffProfile)
def get_staff_profile(
    staff_id: int,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get the profile of a specific staff member.
    Staff members can only access their own profile, while admins can access any staff member's profile.
    Args:
        staff_id (int): ID of the staff member whose profile is to be retrieved.
        current_user (User): The currently authenticated user.
        user_service (UserService): Service for user-related operations.
    Returns:
        StaffProfile: A dictionary containing the staff member's profile information.
    """
    # Check if the user is a staff member accessing their own data or an admin
    if current_user.discriminator not in ["staff", "admin"] or \
       (current_user.discriminator == "staff" and current_user.user_id != staff_id):
        return StaffProfile(
            status="failure",
            message="Unauthorized to access this staff member's profile"
        )

    # Fetch staff profile using the user service
    staff_profile = user_service.get_user_by_id(staff_id)
    if not staff_profile or staff_profile.discriminator != "staff":
        return StaffProfile(
            status="failure",
            message="Staff member not found"
        )

    # Return structured response for staff profile
    return StaffProfile(
        status="success",
        message="Staff profile retrieved successfully",
        staff_id=staff_profile.user_id,
        name=staff_profile.name,
        username=staff_profile.username,
        email=staff_profile.email,
        phone=staff_profile.phone,
        address=staff_profile.address,
        jobtype=staff_profile.jobtype.value if staff_profile.jobtype else None,
        hourly_rate=staff_profile.hourly_rate
    )


@router.get("/{staff_id}/repair-orders", response_model=StaffRepairOrdersResponse)
def get_staff_repair_orders(
    staff_id: int,
    user_service: UserService = Depends(get_user_service),
    repair_order_service: RepairOrderService = Depends(
        get_repair_order_service),
    current_user: User = Depends(get_current_user)
):
    """
    Get all repair orders associated with a specific staff member, including working hours.
    Staff members can only access their own repair orders, while admins can access any staff member's repair orders.
    Args:
        staff_id (int): ID of the staff member.
        user_service (UserService): Service for user-related operations.
        repair_order_service (RepairOrderService): Service for repair order operations.
        current_user (User): The currently authenticated user.
    Returns:
        StaffRepairOrdersResponse: Response containing staff details and their associated repair orders with working hours.
    """
    # Check if the authenticated user has permission to view this staff member's orders
    # For simplicity, allow staff to view their own orders or admin to view any
    if current_user.discriminator not in ["staff", "admin"] or \
       (current_user.discriminator == "staff" and current_user.user_id != staff_id):
        return StaffRepairOrdersResponse(
            status="failure",
            message="Unauthorized to view this staff member's repair orders"
        )

    # Validate staff exists and has the correct role
    staff = user_service.get_user_by_id(staff_id)
    if not staff:
        return StaffRepairOrdersResponse(
            status="failure",
            message="Staff member not found"
        )
    if staff.discriminator != "staff":
        return StaffRepairOrdersResponse(
            status="failure",
            message="User is not a staff member"
        )

    # Fetch repair orders for the staff member, including working hours
    repair_order_data = repair_order_service.get_repair_orders_by_staff_id(
        staff_id)

    # Return structured response
    return StaffRepairOrdersResponse(
        status="success" if repair_order_data else "success_no_data",
        message="Repair orders retrieved successfully" if repair_order_data else "No repair orders found",
        staff_id=staff_id,
        staff_name=staff.name,
        repair_orders=repair_order_data
    )
