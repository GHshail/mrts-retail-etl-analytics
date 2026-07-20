"""MySQL connection helpers shared by ETL and analysis jobs."""

from typing import Any

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import URL


def build_mysql_url(db: dict[str, Any], include_database: bool = True) -> URL:
    """Build a safe MySQL URL; special characters in passwords are handled."""
    return URL.create(
        drivername="mysql+pymysql",
        username=db["username"],
        password=db["password"],
        host=db["host"],
        port=int(db.get("port", 3306)),
        database=db["database"] if include_database else None,
        query={"charset": db.get("charset", "utf8mb4")},
    )


def create_mysql_engine(db: dict[str, Any], include_database: bool = True) -> Engine:
    """Create a pooled SQLAlchemy engine with connection health checks."""
    return create_engine(
        build_mysql_url(db, include_database=include_database),
        pool_pre_ping=True,
        pool_recycle=1800,
        future=True,
    )
