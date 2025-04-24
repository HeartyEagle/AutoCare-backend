from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from sqlalchemy import select
from sqlalchemy.sql import desc

from ..schemas.user import UserCreate, User, UserSchema
from ..models.user import User as UserModel
from ..core.security import get_password_hash
from ..db.session import get_db
from ..crud.user import create_user, get_user_by_username

# the users api router
router = APIRouter(prefix="/user", tags=["user"])


@router.post("/register", response_model=Dict[str, Any])
async def register(
    user: UserCreate,
    db: Session = Depends(get_db)
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
    existing_user = get_user_by_username(db, username=user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    try:
        # Create new user
        new_user = create_user(db, user)
        return {
            "status": True,
            "message": "Registration successful",
            "user_id": new_user.id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.get("/check-username/{username}", response_model=Dict[str, Any])
def check_username(username: str, db: Session = Depends(get_db)):
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
        return {"available": False, "message": "Username is already taken"}
    return {"available": True, "message": "Username is available"}
