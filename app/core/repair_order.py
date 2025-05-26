from ..crud.repair_order import RepairOrderService
from ..crud.repair_assignment import RepairAssignmentService
from ..crud.repair_log import RepairLogService
from ..crud.material import MaterialService
from ..crud.user import UserService
from typing import Optional, List
import random
from ..models.repair import RepairAssignment, RepairLog, Material
from ..models.enums import RepairStatus


def assign_order(order_id: int,
                 repair_order_service: 'RepairOrderService',
                 repair_assignment_service: 'RepairAssignmentService',
                 exclude_staff_id: Optional[int] = None) -> RepairAssignment:
    """
    Assign a repair order to a random eligible staff member based on the required staff type.

    Args:
        order_id (int): ID of the repair order to assign.
        repair_order_service (RepairOrderService): Service for handling repair order operations.
        repair_assignment_service (RepairAssignmentService): Service for handling assignment operations.
        exclude_staff_id (Optional[int]): ID of a staff member to exclude from assignment (for reassignment).

    Returns:
        RepairAssignment: The created assignment object on successful assignment.

    Raises:
        ValueError: If the repair order is not found, required staff type is not specified,
                    or no eligible staff are available.
        RuntimeError: If the assignment creation fails.
    """
    # Fetch the repair order to get required staff type
    repair_order = repair_order_service.get_repair_order_by_id(order_id)
    if not repair_order:
        raise ValueError(f"Repair order with ID {order_id} not found")

    required_staff_type = repair_order.required_staff_type
    if not required_staff_type:
        raise ValueError(
            "Required staff type not specified for this repair order")

    # Fetch eligible staff for the required type, excluding specified staff if provided
    eligible_staff = repair_assignment_service.get_eligible_staff(
        required_staff_type=required_staff_type,
        exclude_staff_id=exclude_staff_id
    )
    if not eligible_staff:
        raise ValueError(f"No eligible staff found for type {required_staff_type}" +
                         (f" excluding staff ID {exclude_staff_id}" if exclude_staff_id else ""))

    # Select a random staff member from the eligible list
    selected_staff = random.choice(eligible_staff)
    staff_id = selected_staff.staff_id if hasattr(
        selected_staff, 'staff_id') else selected_staff.get('staff_id')
    if not staff_id:
        raise RuntimeError("Invalid staff data: staff_id not found")

    # Create a new assignment for the selected staff
    assignment = repair_assignment_service.create_repair_assignment(
        order_id=order_id,
        staff_id=staff_id,
        status="pending"
    )

    if not assignment:
        raise RuntimeError("Failed to create assignment")

    return assignment


def accept_order(assignment_id: int,
                 staff_id: int,
                 accept: bool,
                 repair_order_service: 'RepairOrderService',
                 repair_assignment_service: 'RepairAssignmentService') -> RepairAssignment:
    """
    Handle a staff member's response to an assigned repair order (accept or reject).
    If accepted, update the repair order status to IN_PROGRESS.
    If rejected, reassign the order to another eligible staff member.

    Args:
        assignment_id (int): ID of the assignment to accept or reject.
        staff_id (int): ID of the staff member responding to the assignment.
        accept (bool): True if accepting the assignment, False if rejecting.
        repair_order_service (RepairOrderService): Service for handling repair order operations.
        repair_assignment_service (RepairAssignmentService): Service for handling assignment operations.

    Returns:
        RepairAssignment: The updated assignment object on successful processing.

    Raises:
        ValueError: If the assignment is not found, does not belong to the staff, or is not pending.
        RuntimeError: If updating the assignment or order status fails, or reassignment fails.
    """
    # Fetch the assignment to validate it exists and belongs to the staff
    assignment = repair_assignment_service.get_repair_assignment_by_id(
        assignment_id)
    if not assignment:
        raise ValueError(f"Assignment with ID {assignment_id} not found")
    if assignment.staff_id != staff_id:
        raise ValueError(
            f"Assignment with ID {assignment_id} does not belong to staff ID {staff_id}")
    if assignment.status != "pending":
        raise ValueError(
            f"Assignment with ID {assignment_id} is not in a pending state")

    # Update the assignment status based on the response
    new_status = "accepted" if accept else "rejected"
    updated_assignment = repair_assignment_service.update_assignment_status(
        assignment_id=assignment_id,
        staff_id=staff_id,
        new_status=new_status
    )
    if not updated_assignment:
        raise RuntimeError(
            f"Failed to update assignment status to {new_status}")

    # If accepted, update the repair order status to IN_PROGRESS
    if accept:
        order_id = assignment.order_id
        success = repair_order_service.update_repair_order_status(
            order_id=order_id,
            status=RepairStatus.IN_PROGRESS
        )
        if not success:
            raise RuntimeError(
                f"Failed to update repair order status for order ID {order_id}")

    # If rejected, reassign the order to another eligible staff member
    else:
        order_id = assignment.order_id
        try:
            # Attempt to reassign to another staff member, excluding the current one
            new_assignment = assign_order(
                order_id=order_id,
                repair_order_service=repair_order_service,
                repair_assignment_service=repair_assignment_service,
                exclude_staff_id=staff_id
            )
            if not new_assignment:
                raise RuntimeError(
                    "Reassignment failed: No new assignment created")
        except ValueError as e:
            raise RuntimeError(f"Reassignment failed: {str(e)}")

    return updated_assignment


def calculate_material_fee(
    repair_order_id: int,
    repair_log_service: 'RepairLogService',
    material_service: 'MaterialService'
) -> float:
    """
    Calculate the total material fee for a specific repair order.
    The material fee is the sum of total prices of all materials associated with
    all repair logs under the given repair order.

    Args:
        repair_order_id (int): ID of the repair order to calculate the material fee for.
        repair_log_service (RepairLogService): Service for handling repair log operations.
        material_service (MaterialService): Service for handling material operations.

    Returns:
        float: The total material fee for the repair order. Returns 0.0 if no materials are found.

    Raises:
        ValueError: If the repair order ID is invalid or not found (optional, depending on implementation).
    """
    # Step 1: Fetch all repair logs associated with the repair order
    repair_logs: List[RepairLog] = repair_log_service.get_repair_logs_by_order_id(
        repair_order_id)

    if not repair_logs:
        return 0.0  # Return 0.0 if no repair logs are found for the order

    total_material_fee = 0.0

    # Step 2: Iterate through each repair log to fetch associated materials
    for log in repair_logs:
        # Step 3: Fetch all materials for the current repair log
        materials: List[Material] = material_service.get_materials_by_log_id(
            log.log_id)

        # Step 4: Calculate the total price for materials in this repair log
        for material in materials:
            # Uses the property total_price = quantity * unit_price
            total_material_fee += material.total_price

    return total_material_fee


def calculate_labor_fee(
    repair_order_id: int,
    repair_assignment_service: 'RepairAssignmentService',
    user_service: 'UserService'
) -> float:
    """
    Calculate the total labor fee for a specific repair order.
    The labor fee is the sum of (time_worked * hourly_rate) for all assignments
    associated with the given repair order.

    Args:
        repair_order_id (int): ID of the repair order to calculate the labor fee for.
        repair_assignment_service (RepairAssignmentService): Service for handling repair assignment operations.
        user_service (UserService): Service for handling user (staff) operations to get hourly rate.

    Returns:
        float: The total labor fee for the repair order. Returns 0.0 if no assignments are found
               or if time_worked/hourly_rate data is missing.

    Raises:
        ValueError: If the repair order ID is invalid or not found (optional, depending on implementation).
    """
    # Step 1: Fetch all repair assignments associated with the repair order
    assignments: List[RepairAssignment] = repair_assignment_service.get_assignments_by_order_id(
        repair_order_id)

    if not assignments:
        return 0.0  # Return 0.0 if no assignments are found for the order

    total_labor_fee = 0.0

    # Step 2: Iterate through each assignment to calculate labor fee
    for assignment in assignments:
        # Only calculate fee if time_worked is available
        if assignment.time_worked is not None and assignment.time_worked > 0:
            # Step 3: Fetch staff details to get hourly rate
            staff = user_service.get_user_by_id(assignment.staff_id)
            if staff and staff.discriminator == "staff" and staff.hourly_rate is not None:
                # Step 4: Calculate fee for this assignment (time_worked * hourly_rate)
                assignment_fee = assignment.time_worked * staff.hourly_rate
                total_labor_fee += assignment_fee

    return total_labor_fee
