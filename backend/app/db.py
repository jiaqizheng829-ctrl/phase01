"""Compatibility imports for database access."""

from app.infrastructure.db import (
    SessionLocal,
    check_database_connection,
    engine,
)
