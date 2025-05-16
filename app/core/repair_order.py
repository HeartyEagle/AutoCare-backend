from ..crud.repair_order import RepairOrderService
from ..crud.repair_assignment import RepairAssignmentService
from typing import Optional
import random
from ..models.repair import RepairAssignment
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
        staff_id=staff_id
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
        new_status=new_status
    )
    if not updated_assignment:
        raise RuntimeError(
            f"Failed to update assignment status to {new_status}")

    # If accepted, update the repair order status to IN_PROGRESS
    if accept:
        order_id = assignment.order_id
        success = repair_order_service.update_order_status(
            order_id=order_id,
            new_status=RepairStatus.IN_PROGRESS
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
