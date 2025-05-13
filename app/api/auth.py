from datetime import timedelta
from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from typing import Dict, Any
from ..db.connection import Database
from ..crud.user import UserService
from ..core.security import verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM
from ..core.dependencies import get_db, get_user_service
from ..schemas.auth import UserCreate, UserLogin, Token, RegisterResponse
from ..models.user import User

# The auth API router
router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=Dict[str, Any])
def login(
    login_data: UserLogin,
    user_service: UserService = Depends(get_user_service)
) -> Dict:
    """
    Login endpoint to authenticate a user and return an access token.
    Checks if the username exists, password is correct, and role matches.
    Args:
        login_data (UserLogin): User login data containing username, role, and password.
        user_service (UserService): Service for user-related operations.
    Returns:
        dict: A dictionary indicating success with access token or failure with an error message.
    """
    # Check if user exists
    user = user_service.get_user_by_username(login_data.username)
    if not user:
        return {
            "status": "failure",
            "message": "Incorrect username or password"
        }
        
    # Check if the user's role matches the provided role
    if user.discriminator != login_data.role:
        return {
            "status": "failure",
            "message": "Role does not match. Please check your role selection."
        }
    # Verify password
    if not verify_password(login_data.password, user.password):
        return {
            "status": "failure",
            "message": "Incorrect username or password"
        }
    # Generate access token on successful authentication
    access_token = create_access_token(
        data={"sub": str(user.user_id), "role": user.discriminator},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {
        "status": "success",
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.user_id
    }


@router.post("/verify-token")
def verify_token(
    token_req: Token,
    user_service: UserService = Depends(get_user_service)
):
    """
    Verify the token submitted in the request body.
    Args:
        token_req (Token): Token data.
        user_service (UserService): Service for user-related operations.
    Returns:
        dict: A dictionary containing verification status.
    """
    token = token_req.access_token  # The raw token string
    unauth_response = {
        "status": "failure",
        "message": "Token is invalid or expired"
    }
    try:
        # Decode the token using the same SECRET_KEY and ALGORITHM
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id: str = payload.get("sub")
        if not id:
            print("not username")
            return unauth_response
    except JWTError:
        print("JWTError")
        return unauth_response
    user = user_service.get_user_by_id(id)
    if user is None:
        print("user is None")
        return unauth_response
    return {"status": "success"}


@router.post("/register", response_model=RegisterResponse)
def register(
    user: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    """
    User registration endpoint:
        - Validates username format and uniqueness
        - Validates password strength
        - Creates new user
    Args:
        user (UserCreate): User registration data.
        user_service (UserService): Service for user-related operations.
    Returns:
        dict: A dictionary containing registration status and message.
    """
    # Check if username already exists
    existing_user = user_service.get_user_by_username(user.username)
    if existing_user:
        return {
            "status": "failure",
            "message": "Username already exists"
        }
    try:
        # Create new user
        new_user = user_service.create_customer(user)
        return {
            "status": "success",
            "message": "Registration successful",
            "user_id": new_user.user_id
        }
    except Exception as e:
        return {
            "status": "failure",
            "message": f"Registration failed: {str(e)}"
        }


@router.get("/check-username/{username}", response_model=Dict[str, Any])
def check_username(
    username: str,
    user_service: UserService = Depends(get_user_service)
):
    """
    Check if username is available.
    Args:
        username (str): Username to check.
        user_service (UserService): Service for user-related operations.
    Returns:
        dict: A dictionary containing availability status and message.
    """
    existing_user = user_service.get_user_by_username(username)
    if existing_user:
        return {"status": "failure", "message": "Username is already taken"}
    return {"status": "success", "message": "Username is available"}
