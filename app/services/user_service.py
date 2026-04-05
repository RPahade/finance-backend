"""
User service — business logic for user management and authentication.
"""

from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.schemas.auth import RegisterRequest, LoginRequest
from app.schemas.user import UserUpdateRequest
from app.core.security import hash_password, verify_password, create_access_token
from app.core.exceptions import (
    ConflictException,
    NotFoundException,
    UnauthorizedException,
    BadRequestException,
)


class UserService:
    """Handles user-related business logic."""

    def __init__(self, db: Session):
        self.db = db

    # ----- Authentication -----

    def register(self, data: RegisterRequest) -> User:
        """
        Register a new user. Default role is Viewer.

        Raises:
            ConflictException: If email or username already exists.
        """
        # Check for existing email
        if self.db.query(User).filter(User.email == data.email).first():
            raise ConflictException(
                detail=f"Email '{data.email}' is already registered",
                error_code="EMAIL_EXISTS",
            )

        # Check for existing username
        if self.db.query(User).filter(User.username == data.username).first():
            raise ConflictException(
                detail=f"Username '{data.username}' is already taken",
                error_code="USERNAME_EXISTS",
            )

        user = User(
            email=data.email,
            username=data.username,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            role=UserRole.VIEWER,
            is_active=True,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate(self, data: LoginRequest) -> dict:
        """
        Authenticate a user and return a JWT token payload.

        Raises:
            UnauthorizedException: If credentials are invalid.
        """
        user = self.db.query(User).filter(User.email == data.email).first()

        if not user or not verify_password(data.password, user.hashed_password):
            raise UnauthorizedException(
                detail="Invalid email or password",
                error_code="INVALID_CREDENTIALS",
            )

        if not user.is_active:
            raise UnauthorizedException(
                detail="User account is deactivated",
                error_code="ACCOUNT_INACTIVE",
            )

        access_token = create_access_token(
            data={"sub": user.id, "role": user.role.value}
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "role": user.role.value,
        }

    # ----- User CRUD -----

    def get_all_users(self, page: int = 1, page_size: int = 20) -> tuple[list[User], int]:
        """
        Get paginated list of all users.

        Returns:
            Tuple of (users list, total count).
        """
        query = self.db.query(User)
        total = query.count()
        users = (
            query
            .order_by(User.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return users, total

    def get_user_by_id(self, user_id: int) -> User:
        """
        Get a single user by ID.

        Raises:
            NotFoundException: If user does not exist.
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundException(
                detail=f"User with ID {user_id} not found",
                error_code="USER_NOT_FOUND",
            )
        return user

    def update_user(self, user_id: int, data: UserUpdateRequest, current_user: User) -> User:
        """
        Update user profile, role, or status (admin only).

        Raises:
            NotFoundException: If user does not exist.
            BadRequestException: If admin tries to deactivate themselves.
        """
        user = self.get_user_by_id(user_id)

        # Prevent admin from deactivating themselves
        if data.is_active is False and user.id == current_user.id:
            raise BadRequestException(
                detail="Cannot deactivate your own account",
                error_code="SELF_DEACTIVATION",
            )

        # Apply only the fields that were provided
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        self.db.commit()
        self.db.refresh(user)
        return user

    def deactivate_user(self, user_id: int, current_user: User) -> User:
        """
        Soft-delete (deactivate) a user.

        Raises:
            NotFoundException: If user does not exist.
            BadRequestException: If admin tries to deactivate themselves.
        """
        if user_id == current_user.id:
            raise BadRequestException(
                detail="Cannot deactivate your own account",
                error_code="SELF_DEACTIVATION",
            )

        user = self.get_user_by_id(user_id)
        user.is_active = False
        self.db.commit()
        self.db.refresh(user)
        return user
