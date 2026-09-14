from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


class EmailAlreadyRegisteredError(Exception):
    """Raised when a registration uses an existing email address."""


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def register(self, user_data: UserCreate) -> User:
        normalized_email = str(user_data.email).lower()
        if self.users.get_by_email(normalized_email) is not None:
            raise EmailAlreadyRegisteredError

        try:
            return self.users.create(
                full_name=user_data.full_name,
                email=normalized_email,
                hashed_password=hash_password(user_data.password),
            )
        except IntegrityError as exc:
            self.db.rollback()
            raise EmailAlreadyRegisteredError from exc

    def authenticate(self, email: str, password: str) -> User | None:
        user = self.users.get_by_email(email.lower())
        if user is None or not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user

