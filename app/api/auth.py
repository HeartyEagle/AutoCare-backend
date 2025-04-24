from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import secrets
import base64
from io import BytesIO
from jose import JWTError, jwt

from ..core.security import verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM
from ..crud.user import get_user_by_username
from ..db.session import get_db
from ..schemas.user import UserLogin
from ..schemas.auth import Token
from ..models.user import User

# the auth api router
router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=Token)
def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login endpoint.
    Args:
        login_data (UserLogin): user login data.
        db (Session): database session.
    Returns: 
        dict: a dict containing access_token info.
    Raises:
        HTTPException: if login fails.
    """
    user = get_user_by_username(db, login_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    if not verify_password(login_data.password, user.password):
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    db.commit()

    access_token = create_access_token(
        data={"sub": str(user.user_id)},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/verify-token")
def verify_token(
    token_req: Token,
    db: Session = Depends(get_db)
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
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode the token using the same SECRET_KEY and ALGORITHM
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_by_username(db, username)
    if user is None:
        raise credentials_exception

    return {"valid": True}
