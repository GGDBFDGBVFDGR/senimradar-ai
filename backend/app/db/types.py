import uuid

from sqlalchemy import CHAR, text
from sqlalchemy.types import TypeDecorator

UUID_SERVER_DEFAULT = text("(UUID())")
BOOL_SERVER_DEFAULT = text("0")

MYSQL_TABLE = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_0900_ai_ci",
}


class Guid(TypeDecorator):
    """UUID stored as CHAR(36) so MySQL can keep the dashed form from UUID()."""

    impl = CHAR(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(uuid.UUID(str(value).strip()))

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return uuid.UUID(str(value).strip())
