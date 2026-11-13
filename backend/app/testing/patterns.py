from typing import Any, Dict, List

TEST_ASSERTION_PATTERNS = {
    "bool": "assert result is True",
    "dict": "assert isinstance(result, dict)\n    assert len(result) > 0",
    "list": "assert isinstance(result, list)",
    "str": "assert isinstance(result, str)\n    assert len(result) > 0",
    "int": "assert isinstance(result, int)\n    assert result >= 0",
    "default": "assert result is not None",
}

DEFAULT_ERROR_MAP = {
    "auth": "HTTPException",
    "validate": "ValueError",
    "file": "FileNotFoundError",
    "default": "Exception",
}
