import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.config import settings
from backend.app.models.refresh_token import RefreshToken
from backend.app.models.user import User
from backend.app.schemas.user import UserCreate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_token(token: str) -> str:
    """Deterministic hash of refresh token for DB indexing and safe storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> Tuple[str, int]:
    to_encode = data.copy()
    expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
        expires_in = int(expires_delta.total_seconds())
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
        expires_in = expire_minutes * 60

    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt, expires_in


def generate_refresh_token_string() -> str:
    """Generate high-entropy random refresh token string."""
    return f"rt_{uuid.uuid4().hex}{uuid.uuid4().hex}"


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email.lower().strip()))
    return result.scalars().first()


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.username == username.strip()))
    return result.scalars().first()


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()


async def create_user(db: AsyncSession, user_in: UserCreate, is_superuser: bool = False) -> User:
    # Check for existing email or username
    existing = await db.execute(
        select(User).where(
            or_(
                User.email == user_in.email.lower().strip(),
                User.username == user_in.username.strip(),
            )
        )
    )
    if existing.scalars().first():
        # Will be caught by caller to throw 409
        raise ValueError("User with this email or username already exists")

    hashed_pw = get_password_hash(user_in.password)
    user = User(
        email=user_in.email.lower().strip(),
        username=user_in.username.strip(),
        hashed_password=hashed_pw,
        is_active=True,
        is_superuser=is_superuser,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def store_refresh_token(db: AsyncSession, user_id: uuid.UUID, raw_token: str) -> RefreshToken:
    token_hash = hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    db_token = RefreshToken(
        token_hash=token_hash,
        user_id=user_id,
        expires_at=expires_at,
        revoked=False,
    )
    db.add(db_token)
    await db.commit()
    await db.refresh(db_token)
    return db_token


async def verify_and_rotate_refresh_token(
    db: AsyncSession, raw_token: str
) -> Optional[Tuple[User, str]]:
    token_hash = hash_token(raw_token)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked.is_(False),
        )
    )
    db_token = result.scalars().first()
    if not db_token:
        return None

    # Check expiration
    now_utc = datetime.now(timezone.utc)
    # Handle timezone-aware or naive datetimes safely
    expires_at = db_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < now_utc:
        db_token.revoked = True
        await db.commit()
        return None

    # Fetch user
    user = await get_user_by_id(db, db_token.user_id)
    if not user or not user.is_active:
        return None

    # Revoke old token
    db_token.revoked = True
    
    # Create new access token
    new_access_token, expires_in = create_access_token(
        data={"sub": str(user.id), "email": user.email, "username": user.username}
    )
    await db.commit()

    return user, new_access_token


async def revoke_refresh_tokens_for_user(db: AsyncSession, user_id: uuid.UUID) -> None:
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked.is_(False),
        )
    )
    tokens = result.scalars().all()
    for t in tokens:
        t.revoked = True
    await db.commit()
