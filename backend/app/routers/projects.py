import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database import get_db
from backend.app.dependencies import get_current_user
from backend.app.models.project import ProjectStatus
from backend.app.models.user import User
from backend.app.schemas.common import PaginatedResponse
from backend.app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from backend.app.services.project_service import (
    create_project,
    get_project_by_id,
    list_projects,
    soft_delete_project,
    update_project,
)

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get(
    "",
    response_model=PaginatedResponse[ProjectRead],
    summary="List current user's projects with pagination",
)
async def get_projects(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=50, description="Items per page"),
    status: Optional[ProjectStatus] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total, total_pages = await list_projects(
        db=db, user=current_user, page=page, limit=limit, status=status
    )
    return PaginatedResponse[ProjectRead](
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@router.post(
    "",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
)
async def create_new_project(
    project_in: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await create_project(db, current_user, project_in)
    return project


@router.get(
    "/{id}",
    response_model=ProjectRead,
    summary="Get project by ID with ownership verification",
)
async def get_project(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_by_id(db, id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "not_found",
                "message": "Project not found",
                "status_code": 404,
            },
        )

    # Ownership check: only the owner or a superuser can view
    if project.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "forbidden",
                "message": "You do not have permission to access this project",
                "status_code": 403,
            },
        )

    return project


@router.patch(
    "/{id}",
    response_model=ProjectRead,
    summary="Update project partially with ownership verification",
)
async def patch_project(
    id: uuid.UUID,
    project_update: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_by_id(db, id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "not_found",
                "message": "Project not found",
                "status_code": 404,
            },
        )

    if project.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "forbidden",
                "message": "You do not have permission to modify this project",
                "status_code": 403,
            },
        )

    updated = await update_project(db, project, project_update)
    return updated


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft delete project (sets status to Archived)",
)
async def delete_project(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_by_id(db, id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "not_found",
                "message": "Project not found",
                "status_code": 404,
            },
        )

    if project.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "forbidden",
                "message": "You do not have permission to delete this project",
                "status_code": 403,
            },
        )

    # Soft delete only
    await soft_delete_project(db, project)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
