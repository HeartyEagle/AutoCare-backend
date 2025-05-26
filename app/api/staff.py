# api/staff.py
from fastapi import APIRouter, Depends, HTTPException, status
from ..db.connection import Database
from ..crud.user import UserService
from ..core.dependencies import *
from ..schemas.staff import *
from ..models import User
from ..models.enums import *
from ..core.repair_order import assign_order, accept_order
from typing import Dict

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
    Total hours worked is the sum of time_worked from all repair assignments.
    Only accessible to the staff member themselves.

    Args:
        staff_id (int): ID of the staff member querying their history.
        current_user (User): The currently authenticated user.
        repair_assignment_service (RepairAssignmentService): Service for handling repair assignment operations.

    Returns:
        Dict: Response containing the staff's repair history, total hours worked, and total income.

    Raises:
        HTTPException: If the user is unauthorized or an error occurs during the operation.
    """
    # Validate user is staff and matches the staff_id
    print(current_user.discriminator)
    print(current_user.user_id)
    print(staff_id)
    if (current_user.discriminator != "admin" and current_user.discriminator != "staff") or current_user.user_id != staff_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: Only the staff member can access their own repair history"
        )

    try:
        # Fetch all repair assignments for the staff member
        staff = user_service.get_user_by_id(staff_id)
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

        # Calculate total hours worked by summing time_worked from all assignments
        total_hours_worked = sum(
            assignment.time_worked for assignment in assignments if assignment.time_worked is not None
        )

        # Calculate total income from labor fees
        # Assuming assignment_fee is calculated based on time_worked and hourly rate
        total_income = staff.hourly_rate * total_hours_worked

        # Format the assignment details for the response
        assignment_details = [
            {
                "assignment_id": assignment.assignment_id,
                "order_id": assignment.order_id,
                "status": assignment.status,
                "time_worked": assignment.time_worked if assignment.time_worked is not None else 0.0,
                "assignment_fee": assignment.assignment_fee if assignment.assignment_fee is not None else 0.0
            }
            for assignment in assignments
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
