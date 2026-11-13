import re
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, inspect
from backend.app.database import engine, Base


DESTRUCTIVE_SQL_KEYWORDS = [
    re.compile(r"(?i)\b(insert|update|delete|drop|alter|create|truncate|grant|revoke|exec|execute)\b"),
    re.compile(r"--"),  # comment evasion
    re.compile(r";\s*\w+"),  # multi-statement chaining
]


class DatabaseTool:
    """
    MCP Database Tool.
    Strictly read-only SELECT operations against PostgreSQL database.
    Rejects any DDL, DML, or SQL injection / multi-query attempts.
    """

    @classmethod
    def validate_select_only(cls, query: str):
        trimmed = query.strip()
        if not (trimmed.upper().startswith("SELECT") or trimmed.upper().startswith("WITH")):
            raise ValueError("Only read-only SELECT and WITH queries are permitted.")

        for pat in DESTRUCTIVE_SQL_KEYWORDS:
            if pat.search(trimmed):
                raise ValueError(f"Dangerous or destructive SQL keyword/pattern rejected: {pat.pattern}")

    @classmethod
    async def execute_query(
        cls,
        db: AsyncSession,
        query: str,
        limit: int = 50,
    ) -> Dict[str, Any]:
        try:
            cls.validate_select_only(query)
            limit = min(max(1, limit), 200)

            # Ensure LIMIT clause exists or append it safely
            clean_query = query.rstrip("; \t\n")
            if not re.search(r"(?i)\blimit\s+\d+", clean_query):
                clean_query = f"{clean_query} LIMIT {limit}"

            stmt = text(clean_query)
            result = await db.execute(stmt)

            columns = list(result.keys()) if result.returns_rows else []
            rows = []
            if result.returns_rows:
                raw_rows = result.fetchmany(limit)
                for r in raw_rows:
                    row_dict = {}
                    for col, val in zip(columns, r):
                        # Convert non-serializable objects (e.g. UUID, datetime) to string
                        row_dict[col] = str(val) if val is not None else None
                    rows.append(row_dict)

            return {
                "success": True,
                "query": clean_query,
                "columns": columns,
                "row_count": len(rows),
                "rows": rows,
            }
        except Exception as e:
            return {"success": False, "error": f"Database query error: {str(e)}"}

    @classmethod
    async def inspect_schema(
        cls,
        db: AsyncSession,
        table_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            # Query information_schema safely
            if table_name:
                cols_query = text(
                    "SELECT column_name, data_type, is_nullable "
                    "FROM information_schema.columns "
                    "WHERE table_schema = 'public' AND table_name = :tname "
                    "ORDER BY ordinal_position"
                )
                res = await db.execute(cols_query, {"tname": table_name})
                cols = [
                    {"column": r[0], "type": r[1], "nullable": r[2] == "YES"}
                    for r in res.fetchall()
                ]
                return {
                    "success": True,
                    "table_name": table_name,
                    "columns": cols,
                }
            else:
                tables_query = text(
                    "SELECT table_name "
                    "FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_type = 'BASE TABLE' "
                    "ORDER BY table_name"
                )
                res = await db.execute(tables_query)
                tables = [r[0] for r in res.fetchall()]
                return {
                    "success": True,
                    "tables_count": len(tables),
                    "tables": tables,
                }
        except Exception as e:
            return {"success": False, "error": f"Schema inspection failed: {str(e)}"}
