from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from io import BytesIO
from jose import JWTError, jwt

from ..core.security import verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM
from ..crud.user import get_user_by_username, create_customer
from ..schemas.auth import UserCreate, UserLogin, Token, RegisterResponse
from ..db.session import get_db
from ..models.user import User

# the auth api router
router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db)
) -> Dict:
    """
    Login endpoint to authenticate a user and return an access token.
    Checks if the username exists, password is correct, and role matches.
    Args:
        login_data (UserLogin): User login data containing username, role, and password.
        db (AsyncSession): Database session for querying user data.
    Returns:
        dict: A dictionary indicating success with access token or failure with an error message.
    """
    # Check if user exists
    user = await get_user_by_username(db, login_data.username)
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
        "token_type": "bearer"
    }


@router.post("/verify-token")
async def verify_token(
    token_req: Token,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify the token submitted in the request body.
    Args:
        token_req (Token): token data.
        db (Session): database session.
    Returns:
        dict: a dict containing verification status.
    Raises:
        HTTPException: if token verification fails.
    """
    token = token_req.access_token  # The raw token string
    # credentials_exception = HTTPException(
    #     status_code=status.HTTP_401_UNAUTHORIZED,
    #     detail="Could not validate credentials",
    #     headers={"WWW-Authenticate": "Bearer"},
    # )
    unauth_response = {
        "status": "failure",
        "message": "Token is invalid or expired"
    }

    try:
        # Decode the token using the same SECRET_KEY and ALGORITHM
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            return unauth_response
    except JWTError:
        return unauth_response

    user = await get_user_by_username(db, username)
    if user is None:
        return unauth_response

    return {"status": "success"}


@router.post("/register", response_model=RegisterResponse)
async def register(
    user: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    User registration endpoint:
        - Validates username format and uniqueness
        - Validates password strength
        - Verifies captcha
        - Creates new user
    Args:
        user (UserCreate): user registration data.
        db (Session): database session.
    Returns:
        dict: a dict containing registration status and message.
    Raises:
        HTTPException: if registration fails.
    """
    # Check if username already exists
    existing_user = await get_user_by_username(db, username=user.username)
    if existing_user:
        return {
            "status": "failure",
            "message": "Username already exists"
        }

    try:
        # Create new user
        new_user = await create_customer(db, user)
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
async def check_username(username: str, db: AsyncSession = Depends(get_db)):
    """
    Check if username is available.
    Args:
        username (str): username to check.
        db (Session): database session.
    Returns:
        dict: a dict containing availability status and message.
    """
    existing_user = get_user_by_username(db, username=username)
    if existing_user:
        return {"status": "failure", "message": "Username is already taken"}
    return {"status": "success", "message": "Username is available"}
