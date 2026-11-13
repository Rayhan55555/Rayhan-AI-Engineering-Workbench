import json
from typing import List, Optional, Any
from sqlalchemy import TypeDecorator, Text
from sqlalchemy.dialects.postgresql import dialect as pg_dialect

try:
    from pgvector.sqlalchemy import Vector as PgVector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False
    PgVector = None


class VectorType(TypeDecorator):
    """
    Hybrid Vector type:
    - In PostgreSQL: uses native pgvector Vector(dim)
    - In SQLite (test/in-memory): stores serialized JSON float list
    """
    impl = Text
    cache_ok = True

    def __init__(self, dim: int = 768, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dim = dim

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and PGVECTOR_AVAILABLE:
            return dialect.type_descriptor(PgVector(self.dim))
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value: Optional[List[float]], dialect) -> Any:
        if value is None:
            return None
        if dialect.name == "postgresql" and PGVECTOR_AVAILABLE:
            return value
        # In SQLite / fallback, serialize as JSON string
        return json.dumps([float(x) for x in value])

    def process_result_value(self, value: Any, dialect) -> Optional[List[float]]:
        if value is None:
            return None
        if isinstance(value, list):
            return [float(x) for x in value]
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return [float(x) for x in parsed]
            except Exception:
                pass
        return None
