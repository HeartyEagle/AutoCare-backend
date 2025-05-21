from fastapi import Depends, HTTPException, APIRouter, status, Query
# Assuming these utility functions are available
from ..core.repair_order import calculate_material_fee, calculate_labor_fee
from ..core.dependencies import get_current_user, get_repair_order_service, get_vehicle_service, get_repair_log_service, get_repair_assignment_service, get_material_service, get_user_service, get_repair_request_service
from ..crud.repair_request import RepairRequestService
from ..crud.material import MaterialService
from ..crud.repair_assignment import RepairAssignmentService
from ..crud.repair_log import RepairLogService
from ..crud.vehicle import VehicleService
from ..crud.repair_order import RepairOrderService
from ..models.enums import VehicleType
from ..models.user import User
from typing import Dict, List, Any, Optional
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


router = APIRouter(prefix="/staff", tags=["staff"])


@router.get("/statistics/vehicle-types", response_model=Dict)
def get_vehicle_type_statistics(
    vehicle_type: Optional[str] = Query(
        None, description="Optional vehicle type to filter fault statistics (e.g., SEDAN)"),
    current_user: User = Depends(get_current_user),
    repair_order_service: RepairOrderService = Depends(
        get_repair_order_service),
    vehicle_service: VehicleService = Depends(get_vehicle_service),
    repair_log_service: RepairLogService = Depends(get_repair_log_service),
    repair_assignment_service: RepairAssignmentService = Depends(
        get_repair_assignment_service),
    material_service: MaterialService = Depends(get_material_service),
    user_service: UserService = Depends(get_user_service),
    repair_request_service: RepairRequestService = Depends(
        get_repair_request_service)
):
    """
    Get statistics on repair counts, average repair costs, and repair frequency per vehicle type.
    Optionally, get most common fault types for a specific vehicle type.
    Only accessible to staff and admin users.

    Args:
        vehicle_type (Optional[str]): Optional vehicle type to filter fault statistics (e.g., 'SEDAN').
        current_user (User): The currently authenticated user.
        repair_order_service (RepairOrderService): Service for repair order operations.
        vehicle_service (VehicleService): Service for vehicle operations.
        repair_log_service (RepairLogService): Service for repair log operations.
        repair_assignment_service (RepairAssignmentService): Service for repair assignment operations.
        material_service (MaterialService): Service for material operations.
        user_service (UserService): Service for user (staff) operations.
        repair_request_service (RepairRequestService): Service for repair request operations.

    Returns:
        Dict: Response containing repair statistics per vehicle type and optional fault statistics.

    Raises:
        HTTPException: If the user is unauthorized or an error occurs during retrieval.
    """
    # Check if the user is staff or admin
    if current_user.discriminator not in ["staff", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: Only staff or admin can access vehicle type statistics"
        )

    try:
        # Fetch all repair orders
        repair_orders = repair_order_service.get_all_repair_orders()
        if not repair_orders:
            return {
                "status": "success_no_data",
                "message": "No repair orders found in the system",
                "total_repairs": 0,
                "vehicle_type_frequency": [],
                "vehicle_type_statistics": [],
                "fault_statistics": [] if vehicle_type else []
            }

        # Initialize dictionaries to store stats per vehicle type
        stats_by_type: Dict[str, Dict[str, Any]] = {}
        total_repairs = len(repair_orders)

        # Process each repair order to aggregate statistics
        for order in repair_orders:
            # Fetch the vehicle associated with the repair order
            vehicle = vehicle_service.get_vehicle_by_id(order.vehicle_id)
            if not vehicle or not vehicle.type:
                continue  # Skip if vehicle not found or type not specified

            vehicle_type_str = vehicle.type.value if vehicle.type else "Unknown"

            # Initialize stats for this vehicle type if not already present
            if vehicle_type_str not in stats_by_type:
                stats_by_type[vehicle_type_str] = {
                    "repair_count": 0,
                    "total_cost": 0.0
                }

            # Increment repair count for this vehicle type
            stats_by_type[vehicle_type_str]["repair_count"] += 1

            # Calculate total cost (material fee + labor fee) for this repair order
            material_fee = calculate_material_fee(
                repair_order_id=order.order_id,
                repair_log_service=repair_log_service,
                material_service=material_service
            )
            labor_fee = calculate_labor_fee(
                repair_order_id=order.order_id,
                repair_assignment_service=repair_assignment_service,
                user_service=user_service
            )
            total_cost = material_fee + labor_fee

            # Add to total cost for this vehicle type
            stats_by_type[vehicle_type_str]["total_cost"] += total_cost

        # Format the vehicle type frequency (repair distribution)
        vehicle_type_frequency = [
            {
                "vehicle_type": vehicle_type,
                "repair_count": data["repair_count"],
                "frequency_percentage": (data["repair_count"] / total_repairs * 100) if total_repairs > 0 else 0.0
            }
            for vehicle_type, data in stats_by_type.items()
        ]

        # Format the vehicle type statistics (repair count, average cost, total cost)
        vehicle_type_statistics = [
            {
                "vehicle_type": vehicle_type,
                "repair_count": data["repair_count"],
                "average_cost": data["total_cost"] / data["repair_count"] if data["repair_count"] > 0 else 0.0,
                "total_cost": data["total_cost"]
            }
            for vehicle_type, data in stats_by_type.items()
        ]

        # If a specific vehicle type is provided, calculate most common fault types
        fault_statistics = []
        if vehicle_type:
            try:
                # Validate the vehicle type if provided
                target_vehicle_type = VehicleType[vehicle_type.upper(
                )] if vehicle_type.upper() in VehicleType.__members__ else None
                if not target_vehicle_type:
                    raise ValueError(f"Invalid vehicle type: {vehicle_type}")

                # Fetch repair orders for the specific vehicle type
                fault_counts: Dict[str, int] = {}
                total_repairs_for_type = 0

                for order in repair_orders:
                    vehicle = vehicle_service.get_vehicle_by_id(
                        order.vehicle_id)
                    if vehicle and vehicle.type and vehicle.type.value == target_vehicle_type.value:
                        total_repairs_for_type += 1
                        # Fetch the associated repair request to get the description (assumed to contain fault type)
                        repair_request = repair_request_service.get_repair_request_by_id(
                            order.request_id)
                        if repair_request and repair_request.description:
                            # Extract a simple fault type (for demonstration, assume description is fault type)
                            fault_type = repair_request.description.split(
                            )[0] if repair_request.description else "Unknown Fault"
                            fault_counts[fault_type] = fault_counts.get(
                                fault_type, 0) + 1

                if total_repairs_for_type > 0:
                    fault_statistics = [
                        {
                            "fault_type": fault_type,
                            "count": count,
                            "frequency_percentage": (count / total_repairs_for_type * 100)
                        }
                        # Top 5 faults
                        for fault_type, count in sorted(fault_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                    ]
                else:
                    fault_statistics = []
            except ValueError as e:
                fault_statistics = [{"error": str(e)}]

        return {
            "status": "success",
            "message": "Vehicle type repair statistics retrieved successfully",
            "total_repairs": total_repairs,
            "vehicle_type_frequency": vehicle_type_frequency,
            "vehicle_type_statistics": vehicle_type_statistics,
            "fault_statistics": fault_statistics if vehicle_type else []
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve vehicle type statistics: {str(e)}"
        )
