from typing import Callable, List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_db():
    """Yield a database session, ensuring proper cleanup on exit."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Extract and validate JWT from the Authorization Bearer header.

    Decodes the token payload, looks up the corresponding user in the database,
    and returns the active User instance. Raises 401 if the token is invalid,
    expired, or the user is missing / deactivated.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id: int | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user account",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_role(*roles: str) -> Callable:
    """Return a dependency that enforces the current user has one of the given roles.

    Usage::

        @router.get("/admin-only", dependencies=[Depends(require_role("admin"))])
        def admin_endpoint():
            ...

    Raises 403 Forbidden if the user's role is not in the allowed set.
    """

    def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        allowed: List[str] = list(roles)
        if current_user.role is None or current_user.role.name not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {', '.join(allowed)}",
            )
        return current_user

    return role_checker
