from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system_metadata import SystemMetadata


class SystemMetadataRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, key: str, value: str | None) -> SystemMetadata:
        entry = SystemMetadata(key=key, value=value)
        self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    async def get(self, entry_id: int) -> SystemMetadata | None:
        return await self.session.get(SystemMetadata, entry_id)

    async def get_by_key(self, key: str) -> SystemMetadata | None:
        result = await self.session.execute(
            select(SystemMetadata).where(SystemMetadata.key == key)
        )
        return result.scalar_one_or_none()

    async def list(self, limit: int = 100, offset: int = 0) -> list[SystemMetadata]:
        result = await self.session.execute(
            select(SystemMetadata)
            .order_by(SystemMetadata.id)
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def update(
        self, entry: SystemMetadata, value: str | None
    ) -> SystemMetadata:
        entry.value = value
        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    async def delete(self, entry: SystemMetadata) -> None:
        await self.session.delete(entry)
        await self.session.commit()
