from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database import get_db
from backend.app.dependencies import get_current_user
from backend.app.models.user import User
from backend.app.schemas.user import (
    RefreshTokenRequest,
    RefreshTokenResponse,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserRead,
)
from backend.app.services.auth_service import (
    authenticate_user,
    create_access_token,
    create_user,
    generate_refresh_token_string,
    revoke_refresh_tokens_for_user,
    store_refresh_token,
    verify_and_rotate_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await create_user(db, user_in)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "conflict",
                "message": str(e),
                "status_code": 409,
            },
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and obtain access and refresh tokens",
)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(db, credentials.email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_credentials",
                "message": "Incorrect email or password",
                "status_code": 401,
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "inactive_user",
                "message": "Account is inactive",
                "status_code": 403,
            },
        )

    # Create access token (JWT)
    access_token, expires_in = create_access_token(
        data={"sub": str(user.id), "email": user.email, "username": user.username}
    )

    # Create and persist refresh token in DB
    raw_refresh_token = generate_refresh_token_string()
    await store_refresh_token(db, user.id, raw_refresh_token)

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh_token,
        token_type="bearer",
        expires_in=expires_in,
    )


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    summary="Rotate refresh token and issue new access token",
)
async def refresh_token_endpoint(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await verify_and_rotate_refresh_token(db, body.refresh_token)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_refresh_token",
                "message": "Invalid or expired refresh token",
                "status_code": 401,
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    _, new_access_token = result
    from backend.app.config import settings

    return RefreshTokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke all active refresh tokens for user",
)
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await revoke_refresh_tokens_for_user(db, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/me",
    response_model=UserRead,
    summary="Retrieve current authenticated user profile",
)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user
