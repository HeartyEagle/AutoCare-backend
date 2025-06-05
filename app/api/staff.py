# api/staff.py
from fastapi import APIRouter, Depends, HTTPException, status
from ..db.connection import Database
from ..crud.user import UserService
from ..core.dependencies import *
from ..schemas.staff import *
from ..models import User
from ..models.enums import *
from ..core.repair_order import assign_order, accept_order
from typing import Dict, DefaultDict

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


@router.post("/{user_id}/update-profile", response_model=Dict)
def update_staff_profile(
    user_id: int,
    info: StaffProfileUpdate,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    修改员工（staff）个人信息。员工只能改自己的，admin 可以改所有员工的信息。
    """
    if current_user.discriminator != "admin" and (current_user.discriminator != "staff" or current_user.user_id != user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="not authorized to update this staff member's profile"
        )

    user = user_service.get_user_by_id(user_id)
    if not user or user.discriminator != "staff":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="staff member not found"
        )

    updated = user_service.update_user_info(
        user_id=user_id,
        name=info.name if info.name is not None else user.name,
        email=info.email if info.email is not None else user.email,
        address=info.address if info.address is not None else user.address,
        phone=info.phone if info.phone is not None else user.phone,
        username=info.username if info.username is not None else user.username,
        password=info.password if info.password is not None else None
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="failed to update staff member information"
        )
    return {
        "status": "success",
        "message": "Staff profile updated successfully",
        "user_id": user_id,
        "name": updated.name,
        "email": updated.email,
        "address": updated.address,
        "phone": updated.phone
    }


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


@router.get("/repair-requests", response_model=Dict)
def get_all_repair_requests(
    current_user: User = Depends(get_current_user),
    repair_request_service: RepairRequestService = Depends(
        get_repair_request_service),
    user_service: UserService = Depends(get_user_service),
    vehicle_service: VehicleService = Depends(get_vehicle_service)
):
    """
    Get all repair requests in the system with associated customer and vehicle details.
    Only accessible to staff and admin users.

    Args:
        current_user (User): The currently authenticated user.
        repair_request_service (RepairRequestService): Service for repair request operations.
        user_service (UserService): Service for user-related operations.
        vehicle_service (VehicleService): Service for vehicle-related operations.

    Returns:
        Dict: Response containing a list of all repair requests with customer and vehicle details.

    Raises:
        HTTPException: If the user is unauthorized or an error occurs during retrieval.
    """
    # Check if the user is staff or admin
    if current_user.discriminator not in ["staff", "admin"]:
        return {
            "status": "failure",
            "message": "Unauthorized: Only staff or admin can access all repair requests"
        }

    try:
        # Fetch all repair requests from the system
        repair_requests = repair_request_service.get_all_repair_requests()
        if not repair_requests:
            return {
                "status": "success_no_data",
                "message": "No repair requests found in the system",
                "repair_requests": []
            }

        # Build enriched data for each repair request with customer and vehicle details
        enriched_requests = []
        for request in repair_requests:
            # Fetch customer details
            customer = user_service.get_user_by_id(request.customer_id)
            customer_data = {
                "customer_id": request.customer_id,
                "customer_name": customer.name if customer else "Unknown",
                "customer_phone": customer.phone if customer else "N/A",
                "customer_email": customer.email if customer else "N/A"
            } if customer and customer.discriminator == "customer" else {
                "customer_id": request.customer_id,
                "customer_name": "Unknown",
                "customer_phone": "N/A",
                "customer_email": "N/A"
            }

            # Fetch vehicle details
            vehicle = vehicle_service.get_vehicle_by_id(request.vehicle_id)
            from ..dynpic.dynpic import DynamicImage
            dyn = DynamicImage(enable_cache=True)
            vehicle_data = {
                "vehicle_id": request.vehicle_id,
                "license_plate": vehicle.license_plate if vehicle else "Unknown",
                "brand": vehicle.brand.value if vehicle and vehicle.brand else "N/A",
                "model": vehicle.model if vehicle else "N/A",
                "type": vehicle.type.value if vehicle and vehicle.type else "N/A",
                "color": vehicle.color.value if vehicle and vehicle.color else "N/A",
                "image": dyn.by_keyword(f"{vehicle.brand.value} {vehicle.model} {vehicle.type.value} {vehicle.color.value}"),
                "remarks": vehicle.remarks
            } if vehicle else {
                "vehicle_id": request.vehicle_id,
                "license_plate": "Unknown",
                "brand": "N/A",
                "model": "N/A",
                "type": "N/A",
                "color": "N/A"
            }

            # Combine request data with customer and vehicle details
            enriched_requests.append({
                "request_id": request.request_id,
                "description": request.description,
                "status": request.status,
                "request_time": request.request_time,
                "customer": customer_data,
                "vehicle": vehicle_data
            })

        return {
            "status": "success",
            "message": "Repair requests retrieved successfully",
            "repair_requests": enriched_requests
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve repair requests: {str(e)}"
        )


@router.get("/staff-types", response_model=Dict)
def get_staff_types(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    return {
        "status": "success",
        "staff-types": [type.name[0] + type.name[1:].lower()
                        for type in StaffJobType]
    }


@router.post("/repair-request/{request_id}/generate-order", response_model=Dict)
def generate_repair_order(
    request_id: int,
    repair_order_data: RepairOrderGenerate,
    current_user: User = Depends(get_current_user),
    repair_request_service: RepairRequestService = Depends(
        get_repair_request_service),
    repair_order_service: RepairOrderService = Depends(
        get_repair_order_service),
    repair_assignment_service: RepairAssignmentService = Depends(
        get_repair_assignment_service)
):
    """
    Generate a repair order from a specific repair request.
    Only accessible to staff and admin users.

    Args:
        request_id (int): ID of the repair request to convert into a repair order.
        order_data (Dict): Optional data for the repair order (e.g., required_staff_type, remarks).
        current_user (User): The currently authenticated user.
        repair_request_service (RepairRequestService): Service for repair request operations.
        repair_order_service (RepairOrderService): Service for repair order operations.

    Returns:
        Dict: Response containing the details of the created repair order.

    Raises:
        HTTPException: If the user is unauthorized, the repair request is not found,
                       or the request is already processed.
    """
    # Check if the user is staff or admin
    if current_user.discriminator not in ["staff", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: Only staff or admin can generate repair orders"
        )

    # Fetch the repair request
    repair_request = repair_request_service.get_repair_request_by_id(
        request_id)
    if not repair_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repair request with ID {request_id} not found"
        )

    # Check if the repair request is in a valid state (pending)
    if repair_request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Repair request with ID {request_id} is not in a pending state (current status: {repair_request.status})"
        )

    try:
        # Create a new repair order linked to the repair request
        repair_order = repair_order_service.create_repair_order(
            vehicle_id=repair_request.vehicle_id,
            customer_id=repair_request.customer_id,
            request_id=request_id,
            required_staff_type=repair_order_data.required_staff_type,
            status=RepairStatus.PENDING,
            remarks=repair_order_data.remarks
        )

        # # Update the repair request status to "order_created"
        # repair_request_service.update_repair_request_status(
        #     request_id, "order_created")
        assign_order(repair_order.order_id, repair_order_service,
                     repair_assignment_service)

        return {
            "status": "success",
            "message": "Repair order generated successfully",
            "order_id": repair_order.order_id,
            "request_id": repair_request.request_id,
            "vehicle_id": repair_order.vehicle_id,
            "customer_id": repair_order.customer_id,
            "required_staff_type": repair_order.required_staff_type.value if repair_order.required_staff_type else None,
            "repair_order_status": repair_order.status.value if repair_order.status else None,
            "order_time": str(repair_order.order_time),
            "remarks": repair_order.remarks
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate repair order: {str(e)}"
        )

# Temp Fix


class NewStatus(BaseModel):
    new_status: str  # The new status to set for the repair request


@router.post("/repair-request/{request_id}/update-status", response_model=Dict)
def update_repair_request_status(
    request_id: int,
    new_status: NewStatus,  # The new status to set for the repair request
    current_user: User = Depends(get_current_user),
    repair_request_service: RepairRequestService = Depends(
        get_repair_request_service)
):
    """
    Update the status of a specific repair request.
    Only accessible to staff and admin users.

    Args:
        request_id (int): ID of the repair request to update.
        new_status (str): New status to set for the repair request (e.g., 'pending', 'order_created').
        current_user (User): The currently authenticated user.
        repair_request_service (RepairRequestService): Service for repair request operations.

    Returns:
        Dict: Response containing the updated repair request details.

    Raises:
        HTTPException: If the user is unauthorized, the repair request is not found,
                       or the operation fails.
    """
    # Check if the user is staff or admin
    if current_user.discriminator not in ["staff", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: Only staff or admin can update repair request status"
        )

    try:
        new_status = new_status.new_status
        # Update the repair request status using the service
        updated_request = repair_request_service.update_repair_request_status(
            request_id=request_id,
            new_status=new_status
        )
        if not updated_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repair request with ID {request_id} not found"
            )

        return {
            "status": "success",
            "message": "Repair request status updated successfully",
            "request_id": updated_request.request_id,
            "vehicle_id": updated_request.vehicle_id,
            "customer_id": updated_request.customer_id,
            "description": updated_request.description,
            "new_status": updated_request.status,
            "request_time": updated_request.request_time
        }
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update repair request status: {str(e)}\n{tb}"
        )


@router.get("/{staff_id}/assignments", response_model=Dict)
def get_assignments_for_staff(
    staff_id: int,
    current_user: User = Depends(get_current_user),
    repair_assignment_service: RepairAssignmentService = Depends(
        get_repair_assignment_service)
):
    """
    Get all repair assignments associated with a specific staff member.
    Staff members can only access their own assignments, while admins can access any staff member's assignments.
    """
    if current_user.discriminator not in ["staff", "admin"] or \
       (current_user.discriminator == "staff" and current_user.user_id != staff_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized to view this staff member's assignments"
        )

    assignments = repair_assignment_service.get_assignments_by_staff_id(
        staff_id)
    if not assignments:
        return {
            "status": "success_no_data",
            "message": "No assignments found for this staff member.",
            "staff_id": staff_id,
            "assignments": []
        }

    # You can sort by status or time, if desired:
    assignments_sorted = sorted(assignments, key=lambda a: a.status)

    return {
        "status": "success",
        "message": "Assignments retrieved successfully.",
        "staff_id": staff_id,
        "assignments": [
            {
                "assignment_id": a.assignment_id,
                "order_id": a.order_id,
                "status": a.status,
                "time_worked": a.time_worked
            } for a in assignments_sorted
        ]
    }


@router.post("/{staff_id}/assignments/{assignment_id}/{action}", response_model=Dict)
def handle_assignment(
    staff_id: int,
    assignment_id: int,
    action: str,  # "accept" or "reject"
    current_user: User = Depends(get_current_user),
    repair_order_service: RepairOrderService = Depends(
        get_repair_order_service),
    repair_assignment_service: RepairAssignmentService = Depends(
        get_repair_assignment_service)
):
    """
    Allow staff to accept or reject an assigned repair order.
    If accepted, the repair order status is updated to IN_PROGRESS.
    If rejected, the order is reassigned to another eligible staff member.

    Args:
        staff_id (int): ID of the staff member responding to the assignment.
        assignment_id (int): ID of the assignment to accept or reject.
        action (str): Action to take ("accept" or "reject").
        current_user (User): The currently authenticated user.
        repair_order_service (RepairOrderService): Service for handling repair order operations.
        repair_assignment_service (RepairAssignmentService): Service for handling assignment operations.

    Returns:
        Dict: Response containing the result of the action.

    Raises:
        HTTPException: If the user is unauthorized, the action is invalid, or the operation fails.
    """
    # Validate user is staff and matches the staff_id
    if current_user.discriminator != "staff" or current_user.user_id != staff_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: Only the assigned staff can accept or reject this assignment"
        )

    # Map action to boolean for accept_order function
    if action.lower() == "accept":
        accept = True
    elif action.lower() == "reject":
        accept = False
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action. Use 'accept' or 'reject'"
        )

    try:
        # Call the utility function to handle the acceptance or rejection
        updated_assignment = accept_order(
            assignment_id=assignment_id,
            staff_id=staff_id,
            accept=accept,
            repair_order_service=repair_order_service,
            repair_assignment_service=repair_assignment_service
        )
        response = {
            "status": "success",
            "message": f"Assignment {action}ed successfully",
            "assignment_id": updated_assignment.assignment_id,
            "new_status": updated_assignment.status
        }
        if not accept:
            response["message"] += ". Reassignment attempted."
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Operation failed: {str(e)}"
        )


@router.post("/{staff_id}/repair-log/{log_id}/materials", response_model=Dict)
def record_material(
    staff_id: int,
    log_id: int,
    material_data: MaterialCreate,
    current_user: User = Depends(get_current_user),
    repair_log_service: RepairLogService = Depends(get_repair_log_service),
    material_service: MaterialService = Depends(get_material_service)
):
    """
    Record materials used during a repair process for a specific repair log.
    Only accessible to staff members.

    Args:
        staff_id (int): ID of the staff member recording the material.
        log_id (int): ID of the repair log to associate the material with.
        material_data (MaterialCreate): Data for the material (name, quantity, unit_price, remarks).
        current_user (User): The currently authenticated user.
        repair_log_service (RepairLogService): Service for repair log operations.
        material_service (MaterialService): Service for material operations.

    Returns:
        Dict: Response containing the details of the recorded material.

    Raises:
        HTTPException: If the user is unauthorized, the repair log is not found,
                       or the operation fails.
    """
    # Validate user is staff and matches the staff_id
    if current_user.discriminator != "staff" or current_user.user_id != staff_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: Only the assigned staff can record materials"
        )

    # Validate the repair log exists and belongs to the staff
    repair_log = repair_log_service.get_repair_log_by_id(log_id)
    if not repair_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repair log with ID {log_id} not found"
        )
    if repair_log.staff_id != staff_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Repair log with ID {log_id} does not belong to staff ID {staff_id}"
        )

    try:
        # Create the material record
        material = material_service.create_material(
            log_id=log_id,
            name=material_data.name,
            quantity=material_data.quantity,
            unit_price=material_data.unit_price,
            remarks=material_data.remarks
        )
        return {
            "status": "success",
            "message": "Material recorded successfully",
            "material_id": material.material_id,
            "log_id": material.log_id,
            "name": material.name,
            "quantity": material.quantity,
            "unit_price": material.unit_price,
            "total_price": material.total_price,
            "remarks": material.remarks
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record material: {str(e)}"
        )


@router.post("/{staff_id}/update-repair", response_model=Dict)
def update_repair_progress(
    staff_id: int,
    update_data: RepairUpdate,
    current_user: User = Depends(get_current_user),
    repair_log_service: RepairLogService = Depends(get_repair_log_service),
    repair_order_service: RepairOrderService = Depends(
        get_repair_order_service)
):
    """
    Update repair progress or results by adding a log entry and optionally updating the repair order status.
    Only accessible to staff members.

    Args:
        staff_id (int): ID of the staff member updating the repair progress.
        update_data (RepairUpdate): Data including order_id, log message, and optional new status for the order.
        current_user (User): The currently authenticated user.
        repair_log_service (RepairLogService): Service for repair log operations.
        repair_order_service (RepairOrderService): Service for repair order operations.

    Returns:
        Dict: Response containing the details of the created log entry and updated status (if applicable).

    Raises:
        HTTPException: If the user is unauthorized, the repair order is not found,
                       or the operation fails.
    """
    # Validate user is staff and matches the staff_id
    if current_user.discriminator != "staff" or current_user.user_id != staff_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: Only staff can update repair progress"
        )

    # Validate the repair order exists
    repair_order = repair_order_service.get_repair_order_by_id(
        update_data.order_id)
    if not repair_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repair order with ID {update_data.order_id} not found"
        )

    try:
        # Create a new repair log entry with the progress update or result
        repair_log = repair_log_service.create_repair_log(
            order_id=update_data.order_id,
            staff_id=staff_id,
            log_message=update_data.log_message
        )

        # If a new status is provided, update the repair order status
        if update_data.new_status:
            updated_order = repair_order_service.update_repair_order_status(
                order_id=update_data.order_id,
                status=update_data.new_status
            )
            if not updated_order:
                raise RuntimeError(
                    f"Failed to update repair order status to {update_data.new_status}")

        return {
            "status": "success",
            "message": "Repair progress updated successfully",
            "log_id": repair_log.log_id,
            "order_id": repair_log.order_id,
            "log_message": repair_log.log_message,
            "log_time": repair_log.log_time,
            "new_order_status": update_data.new_status.value if update_data.new_status else None
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update repair progress: {str(e)}"
        )


@router.get("/repair-order/{order_id}/logs", response_model=Dict)
def get_repair_logs_for_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    repair_log_service: RepairLogService = Depends(get_repair_log_service),
    repair_assignment_service: RepairAssignmentService = Depends(
        get_repair_assignment_service)
):
    """
    Get all repair logs for a specific repair order.
    Staff can only access logs if they are assigned to this order. Admin can access any order's logs.
    """
    # 权限校验
    if current_user.discriminator == "staff":
        assignments = repair_assignment_service.get_assignments_by_order_id(
            order_id)
        if not any(a.staff_id == current_user.user_id for a in assignments):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized: Staff can only view logs for orders assigned to them"
            )
    elif current_user.discriminator != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: Only staff (assigned) or admin can access logs"
        )

    logs = repair_log_service.get_repair_logs_by_order_id(order_id)
    if not logs:
        return {
            "status": "success_no_data",
            "message": "No repair logs found for this order.",
            "order_id": order_id,
            "logs": []
        }

    # 可根据实际情况增减返回字段
    return {
        "status": "success",
        "message": "Repair logs retrieved successfully.",
        "order_id": order_id,
        "logs": [
            {
                "log_id": log.log_id,
                "order_id": log.order_id,
                "staff_id": log.staff_id,
                "log_time": log.log_time,
                "log_message": log.log_message
            } for log in logs
        ]
    }


@router.post("/repair-order/{order_id}/finish", response_model=Dict)
def finish_repair_order(
    order_id: int,
    body: FinishOrderRequest,
    current_user: User = Depends(get_current_user),
    repair_order_service: RepairOrderService = Depends(
        get_repair_order_service),
    repair_assignment_service: RepairAssignmentService = Depends(
        get_repair_assignment_service)
):
    """
    Complete a repair order:
    - Set repair order status to COMPLETED
    - Update time_worked for each assignment on this order.

    Only staff/admin can use.

    body: { "time_list": [ {"assignment_id": X, "time_worked": Y}, ... ] }
    """
    # 1. 权限检查
    if current_user.discriminator not in ["staff", "admin"]:
        raise HTTPException(
            status_code=403, detail="Only staff or admin can finish an order")

    # 2. 查找并校验订单
    repair_order = repair_order_service.get_repair_order_by_id(order_id)
    if not repair_order:
        raise HTTPException(
            status_code=404, detail=f"Repair order {order_id} not found")
    if repair_order.status == RepairStatus.COMPLETED:
        raise HTTPException(
            status_code=400, detail=f"Repair order {order_id} is already completed")

    # 3. 更新所有分配的工时
    updated_assignments = []
    for update in body.time_list:
        assignment = repair_assignment_service.update_repair_assignment_time(
            assignment_id=update.assignment_id,
            time_worked=update.time_worked
        )
        if not assignment:
            raise HTTPException(
                status_code=404, detail=f"Assignment {update.assignment_id} not found or update failed")
        updated_assignments.append({
            "assignment_id": assignment.assignment_id,
            "staff_id": assignment.staff_id,
            "new_time_worked": assignment.time_worked
        })

    # 4. 更新维修单状态为已完成
    updated_order = repair_order_service.update_repair_order_status(
        order_id, RepairStatus.COMPLETED)
    if not updated_order:
        raise HTTPException(
            status_code=500, detail=f"Failed to update order status for order {order_id}")

    return {
        "status": "success",
        "message": f"Repair order {order_id} marked as COMPLETED, assignments' time updated.",
        "order_id": order_id,
        "updated_order_status": updated_order.status.value if updated_order.status else None,
        "assignment_time_updates": updated_assignments
    }


@router.get("/{staff_id}/income", response_model=Dict)
def get_staff_income(
    staff_id: int,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
    repair_assignment_service: RepairAssignmentService = Depends(
        get_repair_assignment_service)
):
    """
    Query historical repair records and total labor fee income for a staff member.
    """
    # 权限校验
    if (current_user.discriminator != "admin" and current_user.discriminator != "staff") or current_user.user_id != staff_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: Only the staff member can access their own repair history"
        )
    try:
        staff = user_service.get_user_by_id(staff_id)
        if not staff or staff.discriminator != "staff":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Staff member not found"
            )
        assignments = repair_assignment_service.get_assignments_by_staff_id(
            staff_id)
        if not assignments:
            return {
                "status": "success",
                "message": "No repair assignments found for this staff member",
                "staff_id": staff_id,
                "total_hours_worked": 0.0,
                "total_income": 0.0,
                "assignments": []
            }
        # Use staff's hourly_rate for all assignments
        hourly_rate = getattr(staff, "hourly_rate", 0.0)
        total_hours_worked = sum(a.time_worked or 0.0 for a in assignments)
        total_income = sum((a.time_worked or 0.0) *
                           hourly_rate for a in assignments)
        assignment_details = [
            {
                "assignment_id": a.assignment_id,
                "order_id": a.order_id,
                "status": a.status,
                "time_worked": a.time_worked or 0.0,
                "assignment_fee": (a.time_worked or 0.0) * hourly_rate
            }
            for a in assignments
        ]
        return {
            "status": "success",
            "message": "Repair history retrieved successfully",
            "staff_id": staff_id,
            "total_hours_worked": total_hours_worked,
            "total_income": total_income,
            "assignments": assignment_details
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve repair history: {str(e)}"
        )


@router.get("/{staff_id}/salary-by-month", response_model=Dict)
def get_staff_salary_by_month(
    staff_id: int,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
    repair_order_service: RepairOrderService = Depends(
        get_repair_order_service),
    repair_assignment_service: RepairAssignmentService = Depends(
        get_repair_assignment_service),
    only_completed: bool = True,
):
    """
    返回某维修工的每月薪酬情况（小时总数与收入），升序排列
    Only staff 本人或admin可看。
    """
    # 权限校验
    if current_user.discriminator != "admin" and (current_user.discriminator != "staff" or current_user.user_id != staff_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: Only the staff member or admin can access this data"
        )
    staff = user_service.get_user_by_id(staff_id)
    if not staff or staff.discriminator != "staff":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff not found"
        )

    # Fetch all repair assignments for staff
    assignments = repair_assignment_service.get_assignments_by_staff_id(
        staff_id)
    if not assignments:
        return {"status": "success", "message": "No assignments found", "staff_id": staff_id, "monthly_salary": []}

    # 数组: assignment.assignment_id, assignment.order_id, assignment.time_worked
    # 我们需要获得order_time和order_status
    order_info_map = dict()  # {order_id: (order_time, status)}

    order_ids = {a.order_id for a in assignments}
    # 查所有相关repair_order
    orders = {o.order_id: o for o in repair_order_service.get_all_repair_orders(
    ) if o.order_id in order_ids}
    # 按月聚合
    monthly = DefaultDict(
        lambda: {"total_income": 0.0, "total_hours": 0.0, "order_ids": []})

    for assignment in assignments:
        order = orders.get(assignment.order_id)
        if not order or (only_completed and order.status != RepairStatus.COMPLETED):
            continue
        order_time = order.order_time
        if not order_time:
            continue
        # 支持 order_time 为str或datetime
        try:
            if isinstance(order_time, str):
                order_dt = datetime.fromisoformat(order_time)
            else:
                order_dt = order_time
            month_str = f"{order_dt.year}-{order_dt.month:02d}"
        except Exception:
            continue

        # 工资按单计：只要有time_worked, 就乘以staff.hourly_rate
        time_worked = assignment.time_worked or 0.0
        income = time_worked * staff.hourly_rate
        monthly[month_str]["total_income"] += income
        monthly[month_str]["total_hours"] += time_worked
        if assignment.order_id not in monthly[month_str]["order_ids"]:
            monthly[month_str]["order_ids"].append(assignment.order_id)
    # 整理输出: 按month排序
    result = [
        {
            "month": month,
            "total_income": round(data["total_income"], 2),
            "total_hours": round(data["total_hours"], 2),
            "order_ids": data["order_ids"]
        }
        for month, data in sorted(monthly.items())
    ]
    return {
        "status": "success",
        "staff_id": staff_id,
        "hourly_rate": staff.hourly_rate,
        "monthly_salary": result
    }


@router.post("/assignments/{assignment_id}/update-time", response_model=Dict)
def update_repair_assignment_time(
    assignment_id: int,
    req: UpdateAssignmentTimeRequest,
    current_user: User = Depends(get_current_user),
    repair_assignment_service: RepairAssignmentService = Depends(
        get_repair_assignment_service)
):
    """
    Staff or admin updates own repair assignment time (工时).
    Only the assignment's staff or admin allowed.
    """
    assignment = repair_assignment_service.get_repair_assignment_by_id(
        assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # 权限检查（只能本人或admin改）
    if current_user.discriminator != "admin" and current_user.user_id != assignment.staff_id:
        raise HTTPException(
            status_code=403, detail="Only the assignment's staff or admin can update time.")

    # 更新
    updated = repair_assignment_service.update_repair_assignment_time(
        assignment_id=assignment_id,
        time_worked=req.time_worked
    )
    if not updated:
        raise HTTPException(
            status_code=500, detail="Failed to update assignment time.")

    return {
        "status": "success",
        "message": "Assignment time_worked updated successfully.",
        "assignment_id": updated.assignment_id,
        "order_id": updated.order_id,
        "staff_id": updated.staff_id,
        "time_worked": updated.time_worked
    }
