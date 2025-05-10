from fastapi import APIRouter, Depends
from ..crud.user import UserService
from ..crud.vehicle import VehicleService
from ..crud.repair_request import RepairRequestService
from ..crud.repair_order import RepairOrderService
from ..crud.repair_log import RepairLogService
from ..core.dependencies import *
from ..schemas.customer import *
from ..util.api import object_to_dict

router = APIRouter(prefix="/customer", tags=["customer"])


@router.get("/profile", response_model=CustomerProfile)
def get_customer_profile(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get the profile of the currently authenticated customer.
    Args:
        current_user (User): The currently authenticated user.
        user_service (UserService): Service for user-related operations.
    Returns:
        dict: A dictionary containing the customer's profile information.
    """
    # Fetch customer profile using the user service
    customer_profile = user_service.get_user_by_id(current_user.user_id)

    if not customer_profile:
        return {"status": "failure", "message": "Customer not found"}

    return {
        "status": "success",
        "customer_id": customer_profile.user_id,
        "name": customer_profile.name,
        "username": customer_profile.username,
        "email": customer_profile.email,
        "phone": customer_profile.phone,
        "address": customer_profile.address,
    }


@router.get("/vehicles", response_model=CustomerVehiclesResponse)
def get_customer_vehicles(
    current_user: User = Depends(get_current_user),
    vehicle_service: VehicleService = Depends(get_vehicle_service)
):
    """
    Get the vehicles associated with the currently authenticated customer.
    Args:
        current_user (User): The currently authenticated user.
        vehicle_service (VehicleService): Service for vehicle-related operations.
    Returns:
        dict: A dictionary containing the customer's vehicles.
    """
    # Fetch vehicles for the customer using the vehicle service
    vehicles = vehicle_service.get_vehicles_by_customer_id(
        current_user.user_id)

    if not vehicles:
        return {"status": "failure", "message": "No vehicles found"}

    return {
        "status": "success",
        "customer_id": current_user.user_id,
        "vehicles": [{
            "vehicle_id": vehicle.vehicle_id,
            "license_plate": vehicle.license_plate,
            "brand": vehicle.brand,
            "model": vehicle.model,
            "type": vehicle.type,
            "color": vehicle.color,
        } for vehicle in vehicles]
    }


@router.get("/repair-requests", response_model=CustomerVehiclesResponse)
def get_customer_repair_requests(
    current_user: User = Depends(get_current_user),
    repair_request_service: RepairRequestService = Depends(
        get_repair_request_service),
):
    """
    Get the repair requests associated with the currently authenticated customer.
    Args:
        current_user (User): The currently authenticated user.
        vehicle_service (VehicleService): Service for vehicle-related operations.
    Returns:
        dict: A dictionary containing the customer's repair requests.
    """
    # Fetch repair requests for the customer using the vehicle service
    repair_requests = repair_request_service.get_repair_requests_by_customer_id(
        current_user.user_id)

    if current_user.discriminator != "customer":
        return {"status": "failure", "message": "Not a customer"}

    if not repair_requests:
        return {"status": "failure", "message": "No repair requests found"}

    return {
        "status": "success",
        "customer_id": current_user.user_id,
        "repair_requests": [{
            "request_id": request.request_id,
            "vehicle_id": request.vehicle_id,
            "customer_id": request.customer_id,
            "description": request.description,
            "request_time": request.request_time,
        } for request in repair_requests]
    }


@router.get("/repair-orders", response_model=CustomerRepairOrdersResponse)
def get_customer_repair_orders(
    current_user: User = Depends(get_current_user),
    repair_order_service: RepairOrderService = Depends(
        get_repair_order_service),
):
    """
    Get the repair orders associated with the currently authenticated customer.
    Args:
        current_user (User): The currently authenticated user.
        vehicle_service (VehicleService): Service for vehicle-related operations.
    Returns:
        dict: A dictionary containing the customer's repair orders.
    """
    # Fetch repair orders for the customer using the vehicle service
    repair_orders = repair_order_service.get_repair_orders_by_customer_id(
        current_user.user_id)

    if current_user.discriminator != "customer":
        return {"status": "failure", "message": "Not a customer"}

    if not repair_orders:
        return {"status": "failure", "message": "No repair orders found"}

    return {
        "status": "success",
        "customer_id": current_user.user_id,
        "repair_orders": [object_to_dict(order) for order in repair_orders]
    }


@router.get("/repair-order/{order_id}/repair-logs", response_model=CustomerRepairLogsResponse)
def get_repair_logs(
    order_id: int,
    repair_log_service: RepairLogService = Depends(get_repair_log_service)
):
    repair_logs = repair_log_service.get_repair_logs_by_order_id(order_id)

    if not repair_logs:
        return {"status": "failure", "message": "No repair logs found"}

    return {
        "status": "success",
        "repair_logs": [object_to_dict(log) for log in repair_logs]
    }
