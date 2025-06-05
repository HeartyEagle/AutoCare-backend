# dependencies/auth.py (or wherever this dependency is defined)
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from ..db.connection import Database
from ..crud.user import UserService
from ..crud.vehicle import VehicleService
from ..crud.repair_request import RepairRequestService
from ..crud.repair_order import RepairOrderService
from ..crud.repair_log import RepairLogService
from ..crud.feedback import FeedbackService
from ..crud.repair_assignment import RepairAssignmentService
from ..crud.material import MaterialService
from ..crud.audit import AuditLogService
from ..core.security import SECRET_KEY, ALGORITHM
from ..schemas.auth import TokenPayload
from ..models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_db(request: Request):
    """
    Dependency to get the database instance from app.state.
    Args:
        request (Request): FastAPI request object.
    Returns:
        Database: Database instance stored in app.state.
    """
    return request.app.state.db


def get_user_service(db: Database = Depends(get_db)):
    """
    Dependency to get the UserService instance.
    Args:
        db (Database): Database instance.
    Returns:
        UserService: Instance of UserService for user-related operations.
    """
    return UserService(db)


def get_vehicle_service(db: Database = Depends(get_db)):
    """
    Dependency to get the VehicleService instance.
    Args:
        db (Database): Database instance.
    Returns:
        VehicleService: Instance of VehicleService for vehicle-related operations.
    """
    return VehicleService(db)


def get_repair_request_service(db: Database = Depends(get_db)):
    """
    Dependency to get the RepairRequestService instance.
    Args:
        db (Database): Database instance.
    Returns:
        RepairRequestService: Instance of RepairRequestService for repair request-related operations.
    """
    return RepairRequestService(db)


def get_repair_order_service(db: Database = Depends(get_db)):
    """
    Dependency to get the RepairOrderService instance.
    Args:
        db (Database): Database instance.
    Returns:
        RepairOrderService: Instance of RepairOrderService for repair order-related operations.
    """
    return RepairOrderService(db)


def get_repair_log_service(db: Database = Depends(get_db)):
    return RepairLogService(db)


def get_feedback_service(db: Database = Depends(get_db)):
    return FeedbackService(db)


def get_repair_assignment_service(db: Database = Depends(get_db)):
    return RepairAssignmentService(db)


def get_material_service(db: Database = Depends(get_db)):
    return MaterialService(db)


def get_audit_log_service(db: Database = Depends(get_db)):
    """
    Dependency to get the AuditLogService instance.
    Args:
        db (Database): Database instance.
    Returns:
        AuditLogService: Instance of AuditLogService for audit log-related operations.
    """
    return AuditLogService(db)


def get_current_user(token: str = Depends(oauth2_scheme), user_service: UserService = Depends(get_user_service)):
    """
    Dependency to get the current user from a JWT token.
    Args:
        token (str): JWT token from the request (via OAuth2PasswordBearer).
        user_service (UserService): Service for user-related operations.
    Returns:
        User: The authenticated user object if token is valid and user exists.
    Raises:
        HTTPException: If token validation fails or user is not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)  # Convert user_id from string to int
        token_data = TokenPayload(sub=user_id)
    except (JWTError, ValueError):
        raise credentials_exception
    # Get user from database (synchronous operation)
    user = user_service.get_user_by_id(token_data.sub)
    if user is None:
        raise credentials_exception
    return user
