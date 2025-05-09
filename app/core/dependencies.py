# dependencies/auth.py (or wherever this dependency is defined)
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from db.connection import Database
from ..crud.user import UserService
from core.security import SECRET_KEY, ALGORITHM
from schemas.auth import TokenPayload
from models.user import User

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
