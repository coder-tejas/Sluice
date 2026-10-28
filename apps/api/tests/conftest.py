import os

# Importing app modules requires SLUICE_DATABASE_URL to validate, but unit
# tests never connect. Provide a dummy so collection works without env.
os.environ.setdefault(
    "SLUICE_DATABASE_URL", "postgresql://test:test@localhost:5432/test"
)
