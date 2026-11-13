import math
import uuid
from typing import Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.project import Project, ProjectStatus
from backend.app.models.user import User
from backend.app.schemas.project import ProjectCreate, ProjectUpdate


async def list_projects(
    db: AsyncSession,
    user: User,
    page: int = 1,
    limit: int = 10,
    status: Optional[ProjectStatus] = None,
) -> Tuple[list[Project], int, int]:
    # Users only see their own projects (unless superuser, but even superusers scope by default)
    limit = min(limit, 50)
    offset = (page - 1) * limit

    base_query = select(Project).where(Project.owner_id == user.id)
    if status is not None:
        base_query = base_query.where(Project.status == status)

    # Count total
    count_query = select(func.count()).select_from(base_query.subquery())
    total_count = (await db.execute(count_query)).scalar_one()

    # Get items
    query = base_query.order_by(Project.created_at.desc()).offset(offset).limit(limit)
    items = (await db.execute(query)).scalars().all()
    total_pages = math.ceil(total_count / limit) if total_count > 0 else 0

    return list(items), total_count, total_pages


async def create_project(db: AsyncSession, user: User, project_in: ProjectCreate) -> Project:
    project = Project(
        name=project_in.name,
        description=project_in.description,
        status=project_in.status,
        owner_id=user.id,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


async def get_project_by_id(db: AsyncSession, project_id: uuid.UUID) -> Optional[Project]:
    result = await db.execute(select(Project).where(Project.id == project_id))
    return result.scalars().first()


async def update_project(
    db: AsyncSession, project: Project, project_update: ProjectUpdate
) -> Project:
    update_data = project_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    await db.commit()
    await db.refresh(project)
    return project


async def soft_delete_project(db: AsyncSession, project: Project) -> Project:
    # APPROVAL NOTE: Soft delete only (archived), not hard delete
    project.status = ProjectStatus.Archived
    await db.commit()
    await db.refresh(project)
    return project
