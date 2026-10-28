import os
import sys

from sqlalchemy import create_engine

from alembic import context

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Imported for side effects: registers tables on Base.metadata.
import app.models.model
import app.models.model_version
import app.models.system_metadata  # noqa: F401  (register models)
from app.core.database import Base, get_engine_url

config = context.config
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=get_engine_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(get_engine_url(), pool_pre_ping=True)
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
