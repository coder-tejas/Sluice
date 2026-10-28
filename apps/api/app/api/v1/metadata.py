from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.exceptions import HTTPException

from app.core.database_async import get_async_db
from app.schemas.system_metadata import SystemMetadataCreate, SystemMetadataRead
from app.services.system_metadata import (
    DuplicateKeyError,
    EntryNotFoundError,
    SystemMetadataService,
)

router = APIRouter(
    prefix="/metadata",
    tags=["Metadata"],
)


@router.post(
    "",
    summary="Create a metadata entry",
    status_code=201,
    response_model=SystemMetadataRead,
)
async def create_metadata(
    data: SystemMetadataCreate,
    db: AsyncSession = Depends(get_async_db),
):
    try:
        return await SystemMetadataService(db).create_entry(data)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except DuplicateKeyError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get(
    "/{key}",
    summary="Read a metadata entry by key",
    response_model=SystemMetadataRead,
)
async def read_metadata(
    key: str,
    db: AsyncSession = Depends(get_async_db),
):
    try:
        return await SystemMetadataService(db).get_entry(key)
    except EntryNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete(
    "/{key}",
    summary="Delete a metadata entry by key",
    status_code=204,
)
async def delete_metadata(
    key: str,
    db: AsyncSession = Depends(get_async_db),
):
    try:
        await SystemMetadataService(db).delete_entry(key)
    except EntryNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
