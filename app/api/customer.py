from fastapi import APIRouter, Depends
from ..crud.user import UserService
from ..crud.vehicle import VehicleService
from ..crud.repair_request import RepairRequestService
from ..crud.repair_order import RepairOrderService
from ..crud.repair_log import RepairLogService
from ..core.dependencies import *
from ..schemas.customer import *
from ..util.api import object_to_dict
from ..models.enums import *
from ..models.customer import *
# from ..schemas.customer


router = APIRouter(prefix="/customer", tags=["customer"])


@router.post("/vehicle/add", response_model=AddVehicleResponse)
def add_vehicle(
    new_vehicle: AddVehicle,
    user_service: UserService = Depends(get_user_service),
    vehicle_service: VehicleService = Depends(get_vehicle_service)
):
    new_vehicle_brand = VehicleBrand[new_vehicle.brand.upper()]
    new_vehicle_type = VehicleType[new_vehicle.type.upper()]
    new_vehicle_color = VehicleColor[new_vehicle.color.upper()]

    created_vehicle = vehicle_service.create_vehicle(
        new_vehicle.customer_id,
        new_vehicle.number_plate,
        brand=new_vehicle_brand,
        model=new_vehicle.model,
        type=new_vehicle_type,
        color=new_vehicle_color,
        remarks=new_vehicle.remarks
    )

    if created_vehicle:
        return AddVehicleResponse(
            status="success"
        )
    else:
        return AddVehicleResponse(
            status="failure",
            message="Failed to add vehicle, please try again later."
        )


@router.get("/vehicle/brands", response_model=VehicleBrands)
def get_vehicle_brands(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    return VehicleBrands(
        status="success",
        brands=[brand.name[0] + brand.name[1:].lower()
                for brand in VehicleBrand]
    )


@router.get("/vehicle/colors", response_model=VehicleColors)
def get_vehicle_colors(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    return VehicleColors(
        status="success",
        colors=[color.name[0] + color.name[1:].lower()
                for color in VehicleColor]
    )


@router.get("/vehicle/types", response_model=VehicleTypes)
def get_vehicle_types(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    return VehicleTypes(
        status="success",
        types=[type.name[0] + type.name[1:].lower() for type in VehicleType]
    )


@router.get("/{customer_id}/profile", response_model=CustomerProfile)
def get_customer_profile(
    customer_id: int,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get the profile of a specific customer.
    Customers can only access their own profile, while admins can access any customer's profile.
    Args:
        customer_id (int): ID of the customer whose profile is to be retrieved.
        current_user (User): The currently authenticated user.
        user_service (UserService): Service for user-related operations.
    Returns:
        CustomerProfile: A dictionary containing the customer's profile information.
    """
    # Check if the user is a customer accessing their own data or an admin
    if current_user.discriminator not in ["customer", "admin"] or \
       (current_user.discriminator == "customer" and current_user.user_id != customer_id):
        return CustomerProfile(
            status="failure",
            message="Unauthorized to access this customer's profile"
        )

    # Fetch customer profile using the user service
    customer_profile = user_service.get_user_by_id(customer_id)
    if not customer_profile or customer_profile.discriminator != "customer":
        return CustomerProfile(
            status="failure",
            message="Customer not found"
        )

    return CustomerProfile(
        status="success",
        message="Customer profile retrieved successfully",
        customer_id=customer_profile.user_id,
        name=customer_profile.name,
        username=customer_profile.username,
        email=customer_profile.email,
        phone=customer_profile.phone,
        address=customer_profile.address
    )


@router.post("/{customer_id}/update-profile", response_model=Dict)
def update_customer_profile(
    customer_id: int,
    info: CustomerProfileUpdate,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    修改客户（customer）个人信息。客户只能改自己的，admin 可以改任何客户信息。
    """
    # 权限校验
    if current_user.discriminator != "admin" and (current_user.discriminator != "customer" or current_user.user_id != customer_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this customer's profile"
        )

    user = user_service.get_user_by_id(customer_id)
    if not user or user.discriminator != "customer":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    updated = user_service.update_user_info(
        user_id=customer_id,
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
            detail="Failed to update customer information"
        )
    return {
        "status": "success",
        "message": "Customer profile updated successfully",
        "user_id": customer_id,
        "name": updated.name,
        "email": updated.email,
        "address": updated.address,
        "phone": updated.phone
    }


@router.get("/{customer_id}/vehicles", response_model=CustomerVehiclesResponse)
def get_customer_vehicles(
    customer_id: int,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
    vehicle_service: VehicleService = Depends(get_vehicle_service)
):
    """
    Get the vehicles associated with a specific customer.
    Customers can only access their own vehicles, while admins can access any customer's vehicles.
    Args:
        customer_id (int): ID of the customer whose vehicles are to be retrieved.
        current_user (User): The currently authenticated user.
        user_service (UserService): Service for user-related operations.
        vehicle_service (VehicleService): Service for vehicle-related operations.
    Returns:
        CustomerVehiclesResponse: A dictionary containing the customer's vehicles.
    """
    # Check if the user is a customer accessing their own data or an admin
    if current_user.discriminator not in ["customer", "admin"] or \
       (current_user.discriminator == "customer" and current_user.user_id != customer_id):
        return CustomerVehiclesResponse(
            status="failure",
            message="Unauthorized to access this customer's vehicles"
        )

    # Validate customer exists
    customer = user_service.get_user_by_id(customer_id)
    if not customer or customer.discriminator != "customer":
        return CustomerVehiclesResponse(
            status="failure",
            message="Customer not found"
        )

    # Fetch vehicles for the customer using the vehicle service
    vehicles = vehicle_service.get_vehicles_by_customer_id(customer_id)
    if not vehicles:
        return CustomerVehiclesResponse(
            status="failure",
            message="No vehicles found",
            customer_id=customer_id,
            customer_name=customer.name
        )

    from ..dynpic.dynpic import DynamicImage
    dyn = DynamicImage(enable_cache=True)

    def _vehicle_keyword(vehicle):
        # 任意字段为None时都不会报错
        parts = [
            vehicle.brand.value if vehicle.brand else "",
            vehicle.model or "",
            vehicle.type.value if vehicle.type else "",
            vehicle.color.value if vehicle.color else ""
        ]
        return " ".join([p for p in parts if p]).strip()

    return CustomerVehiclesResponse(
        status="success",
        message="Vehicles retrieved successfully",
        customer_id=customer_id,
        customer_name=customer.name,
        vehicles=[{
            "vehicle_id": vehicle.vehicle_id,
            "license_plate": vehicle.license_plate,
            "brand": vehicle.brand.value if vehicle.brand else "",
            "model": vehicle.model,
            "type": vehicle.type.value if vehicle.type else "",
            "color": vehicle.color.value if vehicle.color else "",
            "image": dyn.by_keyword(_vehicle_keyword(vehicle)),
            "remarks": vehicle.remarks
        } for vehicle in vehicles]
    )


@router.get("/{customer_id}/repair-requests", response_model=CustomerRepairRequestsResponse)
def get_customer_repair_requests(
    customer_id: int,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
    repair_request_service: RepairRequestService = Depends(
        get_repair_request_service)
):
    """
    Get the repair requests associated with a specific customer.
    Customers can only access their own repair requests, while admins can access any customer's repair requests.
    Args:
        customer_id (int): ID of the customer whose repair requests are to be retrieved.
        current_user (User): The currently authenticated user.
        user_service (UserService): Service for user-related operations.
        repair_request_service (RepairRequestService): Service for repair request operations.
    Returns:
        CustomerRepairRequestsResponse: A dictionary containing the customer's repair requests.
    """
    # Check if the user is a customer accessing their own data or an admin
    if current_user.discriminator not in ["customer", "admin"] or \
       (current_user.discriminator == "customer" and current_user.user_id != customer_id):
        return CustomerRepairRequestsResponse(
            status="failure",
            message="Unauthorized to access this customer's repair requests"
        )

    # Validate customer exists
    customer = user_service.get_user_by_id(customer_id)
    if not customer or customer.discriminator != "customer":
        return CustomerRepairRequestsResponse(
            status="failure",
            message="Customer not found"
        )

    # Fetch repair requests for the customer
    repair_requests = repair_request_service.get_repair_requests_by_customer_id(
        customer_id)
    if not repair_requests:
        return CustomerRepairRequestsResponse(
            status="failure",
            message="No repair requests found",
            customer_id=customer_id,
            customer_name=customer.name
        )

    return CustomerRepairRequestsResponse(
        status="success",
        message="Repair requests retrieved successfully",
        customer_id=customer_id,
        customer_name=customer.name,
        repair_requests=[{
            "request_id": request.request_id,
            "vehicle_id": request.vehicle_id,
            "customer_id": request.customer_id,
            "description": request.description,
            "status": request.status,
            "request_time": request.request_time,
        } for request in repair_requests]
    )


@router.get("/{customer_id}/repair-orders", response_model=CustomerRepairOrdersResponse)
def get_customer_repair_orders(
    customer_id: int,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
    repair_order_service: RepairOrderService = Depends(
        get_repair_order_service)
):
    """
    Get the repair orders associated with a specific customer.
    Customers can only access their own repair orders, while admins can access any customer's repair orders.
    Args:
        customer_id (int): ID of the customer whose repair orders are to be retrieved.
        current_user (User): The currently authenticated user.
        user_service (UserService): Service for user-related operations.
        repair_order_service (RepairOrderService): Service for repair order operations.
    Returns:
        CustomerRepairOrdersResponse: A dictionary containing the customer's repair orders.
    """
    # Check if the user is a customer accessing their own data or an admin
    if current_user.discriminator not in ["customer", "admin"] or \
       (current_user.discriminator == "customer" and current_user.user_id != customer_id):
        return CustomerRepairOrdersResponse(
            status="failure",
            message="Unauthorized to access this customer's repair orders"
        )

    # Validate customer exists
    customer = user_service.get_user_by_id(customer_id)
    if not customer or customer.discriminator != "customer":
        return CustomerRepairOrdersResponse(
            status="failure",
            message="Customer not found"
        )

    # Fetch repair orders for the customer
    repair_orders = repair_order_service.get_repair_orders_by_customer_id(
        customer_id)
    if not repair_orders:
        return CustomerRepairOrdersResponse(
            status="failure",
            message="No repair orders found",
            customer_id=customer_id,
            customer_name=customer.name
        )

    return CustomerRepairOrdersResponse(
        status="success",
        message="Repair orders retrieved successfully",
        customer_id=customer_id,
        customer_name=customer.name,
        repair_orders=[object_to_dict(order) for order in repair_orders]
    )


@router.get("/{customer_id}/repair-order/{order_id}/repair-logs", response_model=CustomerRepairLogsResponse)
def get_repair_logs(
    customer_id: int,
    order_id: int,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
    repair_order_service: RepairOrderService = Depends(
        get_repair_order_service),
    repair_log_service: RepairLogService = Depends(get_repair_log_service)
):
    """
    Get the repair logs associated with a specific repair order for a specific customer.
    Customers can only access their own repair logs, while admins can access any customer's repair logs.
    Args:
        customer_id (int): ID of the customer whose repair order logs are to be retrieved.
        order_id (int): ID of the repair order whose logs are to be retrieved.
        current_user (User): The currently authenticated user.
        user_service (UserService): Service for user-related operations.
        repair_order_service (RepairOrderService): Service for repair order operations.
        repair_log_service (RepairLogService): Service for repair log operations.
    Returns:
        CustomerRepairLogsResponse: A dictionary containing the repair logs for the specified order.
    """
    # Check if the user is a customer accessing their own data or an admin
    if current_user.discriminator not in ["customer", "admin"] or \
       (current_user.discriminator == "customer" and current_user.user_id != customer_id):
        return CustomerRepairLogsResponse(
            status="failure",
            message="Unauthorized to access this customer's repair logs"
        )

    # Validate customer exists
    customer = user_service.get_user_by_id(customer_id)
    if not customer or customer.discriminator != "customer":
        return CustomerRepairLogsResponse(
            status="failure",
            message="Customer not found"
        )

    # Validate repair order exists and belongs to the customer
    repair_order = repair_order_service.get_repair_order_by_id(order_id)
    if not repair_order or repair_order.customer_id != customer_id:
        return CustomerRepairLogsResponse(
            status="failure",
            message="Repair order not found or not associated with this customer"
        )

    # Fetch repair logs for the repair order
    repair_logs = repair_log_service.get_repair_logs_by_order_id(order_id)
    if not repair_logs:
        return CustomerRepairLogsResponse(
            status="failure",
            message="No repair logs found",
            customer_id=customer_id,
            order_id=order_id
        )

    return CustomerRepairLogsResponse(
        status="success",
        message="Repair logs retrieved successfully",
        customer_id=customer_id,
        order_id=order_id,
        repair_logs=[object_to_dict(log) for log in repair_logs]
    )


@router.post("/{customer_id}/create-repair-requests", response_model=CustomerRepairRequestCreateResponse)
def create_repair_request(
    customer_id: int,
    request_data: RepairRequestCreate,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
    vehicle_service: VehicleService = Depends(get_vehicle_service),
    repair_request_service: RepairRequestService = Depends(
        get_repair_request_service)
):
    """
    Create a new repair request for a specific customer.
    Customers can only create repair requests for themselves.
    Args:
        customer_id (int): ID of the customer creating the repair request.
        request_data (RepairRequestCreate): Data for the new repair request.
        current_user (User): The currently authenticated user.
        user_service (UserService): Service for user-related operations.
        vehicle_service (VehicleService): Service for vehicle-related operations.
        repair_request_service (RepairRequestService): Service for repair request operations.
    Returns:
        CustomerRepairRequestCreateResponse: Response containing the created repair request details.
    """
    # Check if the user is a customer and is accessing their own data
    if current_user.discriminator != "customer" or current_user.user_id != customer_id:
        return CustomerRepairRequestCreateResponse(
            status="failure",
            message="Unauthorized to create repair request for this customer"
        )

    # Validate customer exists
    customer = user_service.get_user_by_id(customer_id)
    if not customer or customer.discriminator != "customer":
        return CustomerRepairRequestCreateResponse(
            status="failure",
            message="Customer not found"
        )

    # Validate vehicle exists and belongs to the customer
    vehicle = vehicle_service.get_vehicle_by_id(request_data.vehicle_id)
    if not vehicle or vehicle.customer_id != customer_id:
        return CustomerRepairRequestCreateResponse(
            status="failure",
            message="Vehicle not found or not associated with this customer"
        )

    try:
        # Create the repair request using the service
        # Pass status if it exists in request_data, otherwise rely on default in service
        # Default to "pending" if not in request_data
        status = "pending"
        repair_request = repair_request_service.create_repair_request(
            vehicle_id=request_data.vehicle_id,
            customer_id=customer_id,
            description=request_data.description,
            status=status
        )
        return CustomerRepairRequestCreateResponse(
            status="success",
            message="Repair request created successfully",
            request_id=repair_request.request_id,
            vehicle_id=repair_request.vehicle_id,
            customer_id=repair_request.customer_id,
            description=repair_request.description,
            request_status=repair_request.status,  # Include status in response
            request_time=repair_request.request_time
        )
    except Exception as e:
        return CustomerRepairRequestCreateResponse(
            status="failure",
            message=f"Failed to create repair request: {str(e)}"
        )


@router.post("/{customer_id}/repair-order/{order_id}/feedback", response_model=CustomerFeedbackResponse)
def create_feedback(
    customer_id: int,
    order_id: int,
    feedback_data: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
    repair_order_service: RepairOrderService = Depends(
        get_repair_order_service),
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """
    Create feedback for a specific repair order.
    Customers can only provide feedback for their own repair orders. Repair log ID is optional.
    Args:
        customer_id (int): ID of the customer providing feedback.
        order_id (int): ID of the repair order being feedbacked on.
        feedback_data (FeedbackCreate): Data for the feedback including rating, comments, and optional log_id.
        current_user (User): The currently authenticated user.
        user_service (UserService): Service for user-related operations.
        repair_order_service (RepairOrderService): Service for repair order operations.
        feedback_service (FeedbackService): Service for feedback operations.
    Returns:
        CustomerFeedbackResponse: Response containing the created feedback details.
    """
    # Check if the user is a customer and is accessing their own data
    if current_user.discriminator != "customer" or current_user.user_id != customer_id:
        return CustomerFeedbackResponse(
            status="failure",
            message="Unauthorized to provide feedback for this customer"
        )

    # Validate customer exists
    customer = user_service.get_user_by_id(customer_id)
    if not customer or customer.discriminator != "customer":
        return CustomerFeedbackResponse(
            status="failure",
            message="Customer not found"
        )

    # Validate repair order exists and belongs to the customer
    repair_order = repair_order_service.get_repair_order_by_id(order_id)
    if not repair_order or repair_order.customer_id != customer_id:
        return CustomerFeedbackResponse(
            status="failure",
            message="Repair order not found or not associated with this customer"
        )

    # Validate rating is within acceptable range (e.g., 1-5)
    if feedback_data.rating < 1 or feedback_data.rating > 5:
        return CustomerFeedbackResponse(
            status="failure",
            message="Rating must be between 1 and 5"
        )

    try:
        # Create the feedback using the service, log_id is optional from feedback_data
        feedback = feedback_service.create_feedback(
            customer_id=customer_id,
            order_id=order_id,
            log_id=feedback_data.log_id if hasattr(
                # Default to 0 if not provided
                feedback_data, 'log_id') and feedback_data.log_id else 0,
            rating=feedback_data.rating,
            comments=feedback_data.comments
        )
        return CustomerFeedbackResponse(
            status="success",
            message="Feedback submitted successfully",
            feedback_id=feedback.feedback_id,
            customer_id=feedback.customer_id,
            # Return None if default value
            log_id=feedback.log_id if feedback.log_id != 0 else None,
            rating=feedback.rating,
            comments=feedback.comments,
            feedback_time=feedback.feedback_time
        )
    except Exception as e:
        return CustomerFeedbackResponse(
            status="failure",
            message=f"Failed to submit feedback: {str(e)}"
        )


@router.get("/{customer_id}/repair-order/{order_id}/feedbacks", response_model=CustomerFeedbacksResponse)
def get_feedbacks(
    customer_id: int,
    order_id: int,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
    repair_order_service: RepairOrderService = Depends(
        get_repair_order_service),
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """
    Retrieve feedback for a specific repair order.
    Customers can only access feedback for their own repair orders, while admins can access any feedback.

    Args:
        customer_id (int): ID of the customer associated with the repair order.
        order_id (int): ID of the repair order for which feedback is to be retrieved.
        current_user (User): The currently authenticated user.
        user_service (UserService): Service for user-related operations.
        repair_order_service (RepairOrderService): Service for repair order operations.
        feedback_service (FeedbackService): Service for feedback operations.

    Returns:
        CustomerFeedbacksResponse: Response containing the feedback details for the repair order.
    """
    # Check if the user is a customer accessing their own data or an admin
    if current_user.discriminator not in ["customer", "admin"] or \
       (current_user.discriminator == "customer" and current_user.user_id != customer_id):
        return CustomerFeedbacksResponse(
            status="failure",
            message="Unauthorized to access this customer's feedback"
        )

    # Validate customer exists
    customer = user_service.get_user_by_id(customer_id)
    if not customer or customer.discriminator != "customer":
        return CustomerFeedbacksResponse(
            status="failure",
            message="Customer not found"
        )

    # Validate repair order exists and belongs to the customer
    repair_order = repair_order_service.get_repair_order_by_id(order_id)
    if not repair_order or repair_order.customer_id != customer_id:
        return CustomerFeedbacksResponse(
            status="failure",
            message="Repair order not found or not associated with this customer"
        )

    try:
        # Fetch feedback for the repair order
        # Assuming FeedbackService has a method to get feedback by order_id
        feedbacks = feedback_service.get_feedbacks_by_order_id(order_id)
        if not feedbacks:
            return CustomerFeedbacksResponse(
                status="failure",
                message="No feedback found for this repair order",
                customer_id=customer_id,
                order_id=order_id,
                feedbacks=[]
            )

        return CustomerFeedbacksResponse(
            status="success",
            message="Feedback retrieved successfully",
            customer_id=customer_id,
            order_id=order_id,
            feedbacks=[
                {
                    "feedback_id": feedback.feedback_id,
                    "customer_id": feedback.customer_id,
                    "order_id": order_id,
                    "log_id": feedback.log_id if feedback.log_id != 0 else None,
                    "rating": feedback.rating,
                    "comments": feedback.comments,
                    "feedback_time": feedback.feedback_time
                }
                for feedback in feedbacks
            ]
        )
    except Exception as e:
        return CustomerFeedbacksResponse(
            status="failure",
            message=f"Failed to retrieve feedback: {str(e)}"
        )
