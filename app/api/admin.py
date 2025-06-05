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
from ..models.enums import VehicleType, RepairStatus, StaffJobType
from ..models.user import User
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from ..db.connection import Database
from ..crud.user import UserService
from ..core.dependencies import *
from ..schemas.admin import *
from ..schemas.auth import UserCreate, StaffCreate
from ..models import User
from dateutil.relativedelta import relativedelta
import traceback
from ..core.security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta

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
            "address": user.address,
            "jobtype": user.jobtype.value if user.discriminator == "staff" else None,
            "hourly_rate": user.hourly_rate if user.discriminator == "staff" else None
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
        tb = traceback.format_exc()
        detail = (
            f"Failed to retrieve vehicle type statistics: {str(e)}\nTraceback:\n{tb}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)


@router.get("/statistics/cost-analysis", response_model=Dict)
def get_cost_analysis(
    period: str = Query(
        "quarter", description="Time period for analysis: 'quarter' or 'month'"),
    start_date: Optional[str] = Query(
        None, description="Start date for analysis (YYYY-MM-DD), defaults to 1 year ago"),
    end_date: Optional[str] = Query(
        None, description="End date for analysis (YYYY-MM-DD), defaults to now"),
    current_user: User = Depends(get_current_user),
    repair_order_service: RepairOrderService = Depends(
        get_repair_order_service),
    repair_log_service: RepairLogService = Depends(get_repair_log_service),
    repair_assignment_service: RepairAssignmentService = Depends(
        get_repair_assignment_service),
    material_service: MaterialService = Depends(get_material_service),
    user_service: UserService = Depends(get_user_service)
):
    """
    Analyze repair cost composition (labor and material fees) by quarter or month.
    Only accessible to staff and admin users.

    Args:
        period (str): Time period for grouping data, either 'quarter' or 'month' (default: 'quarter').
        start_date (Optional[str]): Start date for analysis (YYYY-MM-DD), defaults to 1 year ago.
        end_date (Optional[str]): End date for analysis (YYYY-MM-DD), defaults to current date.
        current_user (User): The currently authenticated user.
        repair_order_service (RepairOrderService): Service for repair order operations.
        repair_log_service (RepairLogService): Service for repair log operations.
        repair_assignment_service (RepairAssignmentService): Service for repair assignment operations.
        material_service (MaterialService): Service for material operations.
        user_service (UserService): Service for user (staff) operations.

    Returns:
        Dict: Response containing cost analysis grouped by the specified time period.

    Raises:
        HTTPException: If the user is unauthorized, input parameters are invalid, or an error occurs.
    """
    # Check if the user is staff or admin
    if current_user.discriminator not in ["staff", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: Only staff or admin can access cost analysis statistics"
        )

    # Validate period parameter
    if period not in ["quarter", "month"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid period parameter. Use 'quarter' or 'month'"
        )

    try:
        # Set default date range if not provided (last 1 year)
        end_dt = datetime.now() if not end_date else datetime.strptime(end_date, "%Y-%m-%d")
        start_dt = end_dt - \
            relativedelta(years=1) if not start_date else datetime.strptime(
                start_date, "%Y-%m-%d")

        # Validate date range
        if start_dt >= end_dt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date must be before end date"
            )

        # Fetch all repair orders within the date range
        repair_orders = repair_order_service.get_all_repair_orders()
        # Filter orders by date range (assuming order_time is a datetime string or object)
        filtered_orders = [
            order for order in repair_orders
            if order.order_time and start_dt <= datetime.strptime(str(order.order_time), "%Y-%m-%d %H:%M:%S") <= end_dt
        ]

        if not filtered_orders:
            return {
                "status": "success_no_data",
                "message": "No repair orders found in the specified date range",
                "period": period,
                "start_date": start_dt.strftime("%Y-%m-%d"),
                "end_date": end_dt.strftime("%Y-%m-%d"),
                "cost_analysis": []
            }

        # Initialize dictionary to store costs by time period
        cost_by_period: Dict[str, Dict[str, float]] = {}

        # Process each repair order to aggregate costs
        for order in filtered_orders:
            # Determine the period key (year-quarter or year-month)
            order_time = datetime.strptime(
                str(order.order_time), "%Y-%m-%d %H:%M:%S")
            if period == "quarter":
                period_key = f"{order_time.year}-Q{(order_time.month - 1) // 3 + 1}"
            else:  # month
                period_key = f"{order_time.year}-{order_time.month:02d}"

            # Initialize period data if not already present
            if period_key not in cost_by_period:
                cost_by_period[period_key] = {
                    "total_labor_fee": 0.0,
                    "total_material_fee": 0.0,
                    "total_cost": 0.0,
                    "order_count": 0
                }

            # Calculate costs for this repair order
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

            # Aggregate costs for the period
            cost_by_period[period_key]["total_labor_fee"] += labor_fee
            cost_by_period[period_key]["total_material_fee"] += material_fee
            cost_by_period[period_key]["total_cost"] += total_cost
            cost_by_period[period_key]["order_count"] += 1

        # Format the cost analysis results with proportions
        cost_analysis = [
            {
                "period": period_key,
                "total_labor_fee": data["total_labor_fee"],
                "total_material_fee": data["total_material_fee"],
                "total_cost": data["total_cost"],
                "order_count": data["order_count"],
                "labor_fee_percentage": (data["total_labor_fee"] / data["total_cost"] * 100) if data["total_cost"] > 0 else 0.0,
                "material_fee_percentage": (data["total_material_fee"] / data["total_cost"] * 100) if data["total_cost"] > 0 else 0.0
            }
            for period_key, data in sorted(cost_by_period.items())
        ]

        return {
            "status": "success",
            "message": "Cost analysis retrieved successfully",
            "period": period,
            "start_date": start_dt.strftime("%Y-%m-%d"),
            "end_date": end_dt.strftime("%Y-%m-%d"),
            "cost_analysis": cost_analysis
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format or input: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve cost analysis: {str(e)}"
        )


@router.get("/feedback/negative", response_model=Dict)
def get_negative_feedback(
    max_rating: int = Query(
        2, description="Maximum rating to consider as negative feedback (1-5)"),
    current_user: User = Depends(get_current_user),
    feedback_service: FeedbackService = Depends(get_feedback_service),
    repair_order_service: RepairOrderService = Depends(
        get_repair_order_service),
    repair_assignment_service: RepairAssignmentService = Depends(
        get_repair_assignment_service),
    user_service: UserService = Depends(get_user_service)
):
    """
    Retrieve negative feedback for repair orders along with involved staff members.
    Only accessible to staff and admin users.

    Args:
        max_rating (int): Maximum rating value to consider as negative feedback (default: 2).
        current_user (User): The currently authenticated user.
        feedback_service (FeedbackService): Service for feedback operations.
        repair_order_service (RepairOrderService): Service for repair order operations.
        repair_assignment_service (RepairAssignmentService): Service for repair assignment operations.
        user_service (UserService): Service for user (staff) operations.

    Returns:
        Dict: Response containing negative feedback details and associated staff members.

    Raises:
        HTTPException: If the user is unauthorized or an error occurs during retrieval.
    """
    # Check if the user is staff or admin
    if current_user.discriminator not in ["staff", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: Only staff or admin can access negative feedback analysis"
        )

    # Validate max_rating input
    if not 1 <= max_rating <= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="max_rating must be between 1 and 5"
        )

    try:
        # Fetch all negative feedback (rating <= max_rating)
        negative_feedbacks = feedback_service.get_negative_feedbacks(
            max_rating=max_rating)
        if not negative_feedbacks:
            return {
                "status": "success_no_data",
                "message": "No negative feedback found with the specified rating criteria",
                "max_rating": max_rating,
                "feedbacks": []
            }

        # Build enriched data for each negative feedback with repair order and staff details
        enriched_feedbacks = []
        for feedback in negative_feedbacks:
            # Fetch the associated repair order
            repair_order = repair_order_service.get_repair_order_by_id(
                feedback.order_id)
            order_data = {
                "order_id": feedback.order_id,
                "order_status": repair_order.status.value if repair_order and repair_order.status else "Unknown",
                "order_time": repair_order.order_time if repair_order else None,
                "customer_id": repair_order.customer_id if repair_order else feedback.customer_id
            } if repair_order else {
                "order_id": feedback.order_id,
                "order_status": "Unknown",
                "order_time": None,
                "customer_id": feedback.customer_id
            }

            # Fetch staff members assigned to this repair order
            assignments = repair_assignment_service.get_assignments_by_order_id(
                feedback.order_id)
            staff_data = [
                {
                    "staff_id": assignment.staff_id,
                    "assignment_status": assignment.status,
                    "time_worked": assignment.time_worked if assignment.time_worked else 0.0,
                    "staff_name": staff.name if (staff := user_service.get_user_by_id(assignment.staff_id)) and staff.discriminator == "staff" else "Unknown"
                }
                for assignment in assignments
            ] if assignments else []

            # Combine feedback data with order and staff details
            enriched_feedbacks.append({
                "feedback_id": feedback.feedback_id,
                "customer_id": feedback.customer_id,
                "order_id": feedback.order_id,
                "log_id": feedback.log_id if feedback.log_id != 0 else None,
                "rating": feedback.rating,
                "comments": feedback.comments if feedback.comments else "No comments provided",
                "feedback_time": feedback.feedback_time,
                "repair_order": order_data,
                "involved_staff": staff_data
            })

        return {
            "status": "success",
            "message": "Negative feedback retrieved successfully",
            "max_rating": max_rating,
            "feedbacks": enriched_feedbacks
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve negative feedback: {str(e)}"
        )


@router.get("/statistics/job-types", response_model=Dict)
def get_job_type_statistics(
    start_date: Optional[str] = Query(
        None, description="Start date for analysis (YYYY-MM-DD), defaults to 1 year ago"),
    end_date: Optional[str] = Query(
        None, description="End date for analysis (YYYY-MM-DD), defaults to now"),
    current_user: User = Depends(get_current_user),
    repair_order_service: RepairOrderService = Depends(
        get_repair_order_service),
    repair_assignment_service: RepairAssignmentService = Depends(
        get_repair_assignment_service),
    user_service: UserService = Depends(get_user_service)
):
    """
    Analyze the number of tasks assigned to and completed by different job types within a time period,
    including their proportion of total tasks. Useful for hiring decisions.
    Only accessible to staff and admin users.

    Args:
        start_date (Optional[str]): Start date for analysis (YYYY-MM-DD), defaults to 1 year ago.
        end_date (Optional[str]): End date for analysis (YYYY-MM-DD), defaults to current date.
        current_user (User): The currently authenticated user.
        repair_order_service (RepairOrderService): Service for repair order operations.
        repair_assignment_service (RepairAssignmentService): Service for repair assignment operations.
        user_service (UserService): Service for user (staff) operations.

    Returns:
        Dict: Response containing task statistics by job type within the specified time period.

    Raises:
        HTTPException: If the user is unauthorized, input parameters are invalid, or an error occurs.
    """
    # Check if the user is staff or admin
    if current_user.discriminator not in ["staff", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: Only staff or admin can access job type statistics"
        )

    try:
        # Set default date range if not provided (last 1 year)
        end_dt = datetime.now() if not end_date else datetime.strptime(end_date, "%Y-%m-%d")
        start_dt = end_dt - \
            relativedelta(years=1) if not start_date else datetime.strptime(
                start_date, "%Y-%m-%d")

        # Validate date range
        if start_dt >= end_dt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date must be before end date"
            )

        # Fetch all repair orders within the date range
        repair_orders = repair_order_service.get_all_repair_orders()
        # Filter orders by date range (assuming order_time is a datetime string or object)
        filtered_orders = [
            order for order in repair_orders
            if order.order_time and start_dt <= datetime.strptime(str(order.order_time), "%Y-%m-%d %H:%M:%S") <= end_dt
        ]

        total_tasks = len(filtered_orders)
        if total_tasks == 0:
            return {
                "status": "success_no_data",
                "message": "No repair orders found in the specified date range",
                "start_date": start_dt.strftime("%Y-%m-%d"),
                "end_date": end_dt.strftime("%Y-%m-%d"),
                "total_tasks": 0,
                "job_type_statistics": []
            }

        # Initialize dictionary to store stats by job type
        stats_by_job_type: Dict[str, Dict[str, Any]] = {}
        for job_type in StaffJobType:
            stats_by_job_type[job_type.value] = {
                "assigned_tasks": 0,
                "completed_tasks": 0
            }

        # Process each repair order to aggregate statistics by job type
        for order in filtered_orders:
            # Fetch assignments for this repair order
            assignments = repair_assignment_service.get_assignments_by_order_id(
                order.order_id)
            for assignment in assignments:
                # Fetch staff details to get job type
                staff = user_service.get_user_by_id(assignment.staff_id)
                if staff and staff.discriminator == "staff" and staff.jobtype:
                    job_type = staff.jobtype.value
                    # Increment assigned tasks for this job type
                    stats_by_job_type[job_type]["assigned_tasks"] += 1
                    # Increment completed tasks if the assignment status is 'accepted' and order status is 'COMPLETED'
                    if assignment.status == "accepted" and order.status == RepairStatus.COMPLETED:
                        stats_by_job_type[job_type]["completed_tasks"] += 1

        # Format the job type statistics with proportions
        job_type_statistics = [
            {
                "job_type": job_type,
                "assigned_tasks": data["assigned_tasks"],
                "assigned_percentage": (data["assigned_tasks"] / total_tasks * 100) if total_tasks > 0 else 0.0,
                "completed_tasks": data["completed_tasks"],
                "completed_percentage": (data["completed_tasks"] / total_tasks * 100) if total_tasks > 0 else 0.0
            }
            for job_type, data in stats_by_job_type.items()
            # Only include job types with assignments
            if data["assigned_tasks"] > 0
        ]

        return {
            "status": "success",
            "message": "Job type task statistics retrieved successfully",
            "start_date": start_dt.strftime("%Y-%m-%d"),
            "end_date": end_dt.strftime("%Y-%m-%d"),
            "total_tasks": total_tasks,
            "job_type_statistics": job_type_statistics
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format or input: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve job type statistics: {str(e)}"
        )


@router.get("/statistics/uncompleted-tasks", response_model=Dict)
def get_uncompleted_tasks_statistics(
    current_user: User = Depends(get_current_user),
    repair_order_service: RepairOrderService = Depends(
        get_repair_order_service),
    repair_assignment_service: RepairAssignmentService = Depends(
        get_repair_assignment_service),
    vehicle_service: VehicleService = Depends(get_vehicle_service),
    user_service: UserService = Depends(get_user_service)
):
    """
    Analyze uncompleted repair tasks/orders (not in COMPLETED status) up to the current date.
    Provides counts and breakdowns by job type, staff member, and vehicle type.
    Only accessible to staff and admin users.

    Args:
        current_user (User): The currently authenticated user.
        repair_order_service (RepairOrderService): Service for repair order operations.
        repair_assignment_service (RepairAssignmentService): Service for repair assignment operations.
        vehicle_service (VehicleService): Service for vehicle operations.
        user_service (UserService): Service for user (staff) operations.

    Returns:
        Dict: Response containing statistics on uncompleted tasks by job type, staff, and vehicle type.

    Raises:
        HTTPException: If the user is unauthorized or an error occurs during retrieval.
    """
    # Check if the user is staff or admin
    if current_user.discriminator not in ["staff", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: Only staff or admin can access uncompleted task statistics"
        )

    try:
        # Fetch all repair orders
        repair_orders = repair_order_service.get_all_repair_orders()
        # Filter for uncompleted orders (status != COMPLETED)
        uncompleted_orders = [
            order for order in repair_orders
            if order.status != RepairStatus.COMPLETED
        ]

        total_uncompleted_tasks = len(uncompleted_orders)
        if total_uncompleted_tasks == 0:
            return {
                "status": "success_no_data",
                "message": "No uncompleted repair tasks found in the system",
                "total_uncompleted_tasks": 0,
                "by_job_type": [],
                "by_staff": [],
                "by_vehicle_type": []
            }

        # Initialize dictionaries for statistics
        stats_by_job_type: Dict[str, Dict[str, Any]] = {
            job_type.value: {"count": 0} for job_type in StaffJobType}
        stats_by_staff: Dict[int, Dict[str, Any]] = {}
        stats_by_vehicle_type: Dict[str, Dict[str, Any]] = {
            vehicle_type.value: {"count": 0} for vehicle_type in VehicleType}
        stats_by_vehicle_type["Unknown"] = {
            "count": 0}  # For vehicles with no type

        # Process each uncompleted order to aggregate statistics
        for order in uncompleted_orders:
            # Fetch assignments for this repair order to get job type and staff
            assignments = repair_assignment_service.get_assignments_by_order_id(
                order.order_id)
            for assignment in assignments:
                staff = user_service.get_user_by_id(assignment.staff_id)
                if staff and staff.discriminator == "staff" and staff.jobtype:
                    job_type = staff.jobtype.value
                    stats_by_job_type[job_type]["count"] += 1

                    # Aggregate by staff member
                    if assignment.staff_id not in stats_by_staff:
                        stats_by_staff[assignment.staff_id] = {
                            "staff_name": staff.name if staff.name else "Unknown",
                            "job_type": job_type,
                            "count": 0
                        }
                    stats_by_staff[assignment.staff_id]["count"] += 1

            # Fetch vehicle details to get vehicle type
            vehicle = vehicle_service.get_vehicle_by_id(order.vehicle_id)
            vehicle_type = vehicle.type.value if vehicle and vehicle.type else "Unknown"
            stats_by_vehicle_type[vehicle_type]["count"] += 1

        # Format statistics for response
        job_type_stats = [
            {
                "job_type": job_type,
                "count": data["count"],
                "percentage": (data["count"] / total_uncompleted_tasks * 100) if total_uncompleted_tasks > 0 else 0.0
            }
            for job_type, data in stats_by_job_type.items()
            # Only include job types with uncompleted tasks
            if data["count"] > 0
        ]

        staff_stats = [
            {
                "staff_id": staff_id,
                "staff_name": data["staff_name"],
                "job_type": data["job_type"],
                "count": data["count"],
                "percentage": (data["count"] / total_uncompleted_tasks * 100) if total_uncompleted_tasks > 0 else 0.0
            }
            for staff_id, data in stats_by_staff.items()
        ]

        vehicle_type_stats = [
            {
                "vehicle_type": vehicle_type,
                "count": data["count"],
                "percentage": (data["count"] / total_uncompleted_tasks * 100) if total_uncompleted_tasks > 0 else 0.0
            }
            for vehicle_type, data in stats_by_vehicle_type.items()
            # Only include vehicle types with uncompleted tasks
            if data["count"] > 0
        ]

        return {
            "status": "success",
            "message": "Uncompleted repair task statistics retrieved successfully",
            "total_uncompleted_tasks": total_uncompleted_tasks,
            "by_job_type": job_type_stats,
            "by_staff": staff_stats,
            "by_vehicle_type": vehicle_type_stats
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve uncompleted task statistics: {str(e)}"
        )


@router.post("/create-user", response_model=Dict)
def admin_create_user(
    user_data: dict,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Admin creates a new user (customer/staff/admin).
    """
    if current_user.discriminator != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can create users"
        )

    # Dynamic check/dispatch by discriminator
    discriminator = user_data.get("discriminator")
    if discriminator == "customer":
        try:
            req = CustomerCreate(**user_data)
            created = user_service.create_customer(UserCreate(
                name=req.name,
                username=req.username,
                password=req.password,
                phone=req.phone,
                email=req.email,
                address=req.address
            ))
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to create customer: {e}")
        return {
            "status": "success",
            "message": "Customer created successfully",
            "user_id": created.user_id,
            "username": created.username,
            "email": created.email,
            "discriminator": "customer"
        }
    elif discriminator == "staff":
        try:
            req = StaffCreateRequest(**user_data)
            created = user_service.create_staff(StaffCreate(
                name=req.name,
                username=req.username,
                password=req.password,
                phone=req.phone,
                email=req.email,
                address=req.address,
                jobtype=req.jobtype,
                hourly_rate=req.hourly_rate
            ))
        except Exception as e:
            tb = traceback.format_exc()
            raise HTTPException(
                status_code=400,
                detail=f"Failed to create staff: {str(e)}\nTraceback:\n{tb}"
            )
        return {
            "status": "success",
            "message": "Staff created successfully",
            "user_id": created.user_id,
            "username": created.username,
            "email": created.email,
            "jobtype": created.jobtype.value if created.jobtype else None,
            "hourly_rate": created.hourly_rate,
            "discriminator": "staff"
        }
    elif discriminator == "admin":
        try:
            req = AdminCreate(**user_data)
            created = user_service.create_admin(UserCreate(
                name=req.name,
                username=req.username,
                password=req.password,
                phone=req.phone,
                email=req.email,
                address=req.address
            ))
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to create admin: {e}")
        return {
            "status": "success",
            "message": "Admin created successfully",
            "user_id": created.user_id,
            "username": created.username,
            "email": created.email,
            "discriminator": "admin"
        }
    else:
        raise HTTPException(
            status_code=400, detail="discriminator must be one of: customer, staff, admin")


@router.post("/update-user-profile/{user_id}", response_model=Dict)
def admin_update_user_profile(
    user_id: int,
    update: AdminUpdateUserProfileReq,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Admin updates any user's profile (base fields: name, email, address, phone; staff: jobtype, hourly_rate).
    """
    if current_user.discriminator != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can update user profiles"
        )

    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # First, update the basic user fields (name, email, address, phone)
    updated_user = user_service.update_user_info(
        user_id=user_id,
        name=update.name if update.name is not None else user.name,
        email=update.email if update.email is not None else user.email,
        address=update.address if update.address is not None else user.address,
        phone=update.phone if update.phone is not None else user.phone
    )

    # If staff, update staff details（jobtype/hourly_rate）
    staff_fields_updated = False
    if user.discriminator == "staff" and (update.jobtype is not None or update.hourly_rate is not None):
        # update staff 表
        staff_data = {}
        if update.jobtype is not None:
            staff_data["jobtype"] = update.jobtype.value
        if update.hourly_rate is not None:
            staff_data["hourly_rate"] = update.hourly_rate
        if staff_data:
            user_service.db.update_data(
                table_name="staff",
                data=staff_data,
                where=f"staff_id = {user.user_id}"
            )
            # for audit
            staff_fields_updated = True

    return {
        "status": "success",
        "message": "user info updated" + (", staff additional info also updated" if staff_fields_updated else ""),
        "user_id": user_id,
        "updated_fields": update.model_dump(exclude_unset=True),
        "discriminator": user.discriminator
    }


@router.get("/get-token/{user_id}", response_model=Dict)
def get_user_token_by_id(
    user_id: int,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    管理员为指定用户（user_id）生成JWT访问token（模拟用户登录）。
    """
    if current_user.discriminator != "admin":
        raise HTTPException(
            status_code=403, detail="Only admin can get user token.")

    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # 这里直接用sub/role。根据实际需求可加更多字段
    access_token = create_access_token(
        data={"sub": str(user.user_id), "role": user.discriminator},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "status": "success",
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.user_id,
        "role": user.discriminator
    }


@router.get("/logs", response_model=Dict)
def get_audit_logs(
    table_name: Optional[str] = Query(
        None, description="Filter by table name"),
    operation: Optional[str] = Query(
        None, description="Filter by operation type, e.g. INSERT/UPDATE/DELETE"),
    limit: int = Query(100, ge=1, le=1000,
                       description="Maximum logs to return"),
    current_user: User = Depends(get_current_user),
    audit_log_service: AuditLogService = Depends(get_audit_log_service)
):
    """
    Admin API: view (optionally filter) audit logs. Newest first.
    """
    if current_user.discriminator != "admin":
        raise HTTPException(
            status_code=403, detail="Only admin can view audit logs")

    logs = audit_log_service.get_audit_logs(
        table_name=table_name,
        operation=operation,
        limit=limit
    )
    return {
        "status": "success",
        "logs": [
            {
                "log_id": log.log_id,
                "table_name": log.table_name,
                "record_id": log.record_id,
                "operation": str(log.operation),
                "old_data": log.old_data,
                "new_data": log.new_data,
                "operated_at": str(log.operated_at)
            }
            for log in logs
        ]
    }


@router.delete("/repair-order/{order_id}", response_model=Dict)
def admin_delete_repair_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    repair_order_service: RepairOrderService = Depends(
        get_repair_order_service)
):
    """
    Admin deletes a repair order (级联/关联表数据由DB或业务自动处理).
    """
    if current_user.discriminator != "admin":
        raise HTTPException(
            status_code=403, detail="Only admin can delete repair orders.")

    deleted_order = repair_order_service.delete_repair_order(order_id)
    if not deleted_order:
        raise HTTPException(status_code=404, detail="Repair order not found")

    return {
        "status": "success",
        "message": f"Repair order {order_id} deleted successfully",
        "order": {
            "order_id": deleted_order.order_id,
            "vehicle_id": deleted_order.vehicle_id,
            "customer_id": deleted_order.customer_id,
            "status": deleted_order.status.value if deleted_order.status else None,
            "order_time": str(deleted_order.order_time)
        }
    }


@router.delete("/delete-user/{user_id}", response_model=Dict)
def admin_delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    管理员删除任意用户（包括admin, staff, customer），级联清理子表。
    """
    if current_user.discriminator != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can delete users"
        )

    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    success = user_service.delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to delete user, please check if the user exists or has related data"
        )

    return {
        "status": "success",
        "message": f"{user.discriminator.capitalize()}(ID: {user.user_id}) deleted successfully",
        "user_id": user.user_id,
        "discriminator": user.discriminator,
        "name": user.name,
        "username": user.username
    }


@router.post("/rollback/last", response_model=Dict)
def rollback_last_audit_operation(
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_db),
    audit_log_service=Depends(get_audit_log_service)
):
    """
    Admin API: Roll back the most recent audit log operation (no params needed).
    """
    if current_user.discriminator != "admin":
        raise HTTPException(
            status_code=403, detail="Only admin can rollback the last operation.")
    try:
        msg = audit_log_service.rollback_most_recent(db)
        return {
            "status": "success",
            "message": msg
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Rollback failed: {str(e)}")


@router.post("/rollback/{record_id}", response_model=Dict)
def admin_rollback_last_change(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_db),
    audit_log_service=Depends(get_audit_log_service)
):
    if current_user.discriminator != "admin":
        raise HTTPException(
            status_code=403, detail="Only admin can rollback records")

    try:
        msg = audit_log_service.rollback_last_operation(db, record_id)
        return {
            "status": "success",
            "message": msg,
            "record_id": record_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Rollback failed: {str(e)}")
