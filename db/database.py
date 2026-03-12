"""
Database connection manager for Supabase PostgreSQL.

Provides a context-managed connection pool so callers never
have to worry about closing connections or cursors.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator

import psycopg2
import psycopg2.extras
from psycopg2.extensions import connection as PgConnection

from config import DATABASE_URL

logger = logging.getLogger(__name__)

# ── Module-level connection pool (simple single-connection approach) ──────────

_connection: PgConnection | None = None


def get_connection() -> PgConnection:
    """Return a reusable database connection, creating one if needed."""
    global _connection
    if _connection is None or _connection.closed:
        logger.info("Opening new database connection …")
        _connection = psycopg2.connect(DATABASE_URL)
        _connection.autocommit = False
    return _connection


@contextmanager
def get_cursor() -> Generator[psycopg2.extras.DictCursor, None, None]:
    """
    Yield a database cursor inside a managed transaction.

    * Commits on success.
    * Rolls back on exception and re-raises.
    """
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("Database error — transaction rolled back")
        raise
    finally:
        cursor.close()


def close_connection() -> None:
    """Close the module-level connection if it is open."""
    global _connection
    if _connection and not _connection.closed:
        _connection.close()
        logger.info("Database connection closed.")
    _connection = None
