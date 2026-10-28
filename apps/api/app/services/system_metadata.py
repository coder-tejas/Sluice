"""Application logic for system metadata.

Owns validation, transactions and response shaping. Callers (API)
deal in schemas and domain errors, never in SQLAlchemy objects.
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system_metadata import SystemMetadata
from app.repositories.system_metadata import SystemMetadataRepository
from app.schemas.system_metadata import SystemMetadataCreate, SystemMetadataRead

MAX_KEY_LENGTH = 128
MAX_VALUE_LENGTH = 512


class DuplicateKeyError(Exception):
    def __init__(self, key: str):
        super().__init__(f"metadata key already exists: {key}")
        self.key = key


class EntryNotFoundError(Exception):
    def __init__(self, key: str):
        super().__init__(f"metadata entry not found: {key}")
        self.key = key


class SystemMetadataService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = SystemMetadataRepository(session)

    @staticmethod
    def _validate(key: str, value: str | None) -> None:
        if not key or not key.strip():
            raise ValueError("key must not be blank")
        if len(key) > MAX_KEY_LENGTH:
            raise ValueError(f"key must be at most {MAX_KEY_LENGTH} characters")
        if value is not None and len(value) > MAX_VALUE_LENGTH:
            raise ValueError(f"value must be at most {MAX_VALUE_LENGTH} characters")

    @staticmethod
    def _read(entry: SystemMetadata) -> SystemMetadataRead:
        return SystemMetadataRead.model_validate(entry)

    async def create_entry(self, data: SystemMetadataCreate) -> SystemMetadataRead:
        self._validate(data.key, data.value)
        try:
            entry = await self.repo.create(data.key, data.value)
        except IntegrityError:
            await self.session.rollback()
            raise DuplicateKeyError(data.key)
        return self._read(entry)

    async def get_entry(self, key: str) -> SystemMetadataRead:
        entry = await self.repo.get_by_key(key)
        if entry is None:
            raise EntryNotFoundError(key)
        return self._read(entry)

    async def list_entries(
        self, limit: int = 100, offset: int = 0
    ) -> list[SystemMetadataRead]:
        return [self._read(e) for e in await self.repo.list(limit, offset)]

    async def update_entry(
        self, key: str, value: str | None
    ) -> SystemMetadataRead:
        self._validate(key, value)
        entry = await self.repo.get_by_key(key)
        if entry is None:
            raise EntryNotFoundError(key)
        return self._read(await self.repo.update(entry, value))

    async def delete_entry(self, key: str) -> None:
        entry = await self.repo.get_by_key(key)
        if entry is None:
            raise EntryNotFoundError(key)
        await self.repo.delete(entry)
