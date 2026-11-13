from pathlib import Path
from typing import Set

# Project root (workspace root)
PROJECT_ROOT = Path("/app/applet").resolve()

# Allowed file extensions for reading/inspection
ALLOWED_EXTENSIONS: Set[str] = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".json",
    ".md",
    ".txt",
    ".yaml",
    ".yml",
    ".toml",
    ".example",
    ".sql",
    ".html",
    ".css",
}

# Maximum allowed file size: 500 KB
MAX_FILE_SIZE_BYTES = 500 * 1024

# Explicitly blocked path keywords or patterns
BLOCKED_PATTERNS = [
    "/etc",
    "/proc",
    "/sys",
    "/root",
    "/var",
    ".git/",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
]

# Specifically blocked filenames (secrets/credentials)
BLOCKED_EXACT_FILES = {
    ".env",
    ".env.local",
    ".env.production",
    "id_rsa",
    "id_ed25519",
}


class SandboxSecurityError(Exception):
    """Raised when an operation violates sandbox security boundaries."""
    pass


def resolve_safe_path(requested_path: str, base_dir: Path = PROJECT_ROOT) -> Path:
    """
    Safely resolves a path relative to the project root.
    Blocks directory traversal (../), absolute path escaping,
    and sensitive files/directories.
    """
    raw_str = requested_path.strip()
    if not raw_str:
        raise SandboxSecurityError("Path cannot be empty.")

    # Remove leading slash or relative prefix if provided
    clean_str = raw_str.lstrip("/")
    if clean_str.startswith("./"):
        clean_str = clean_str[2:]

    # Resolve target path
    candidate = (base_dir / clean_str).resolve()

    # 1. Enforce that candidate is strictly inside base_dir
    try:
        candidate.relative_to(base_dir)
    except ValueError:
        raise SandboxSecurityError(
            f"Path traversal detected: '{requested_path}' escapes the workspace root."
        )

    # 2. Block sensitive keywords / path segments
    path_str = str(candidate)
    for pattern in BLOCKED_PATTERNS:
        if pattern in path_str:
            raise SandboxSecurityError(
                f"Access to restricted path pattern '{pattern}' is blocked."
            )

    # 3. Block sensitive files like .env (except .env.example)
    filename = candidate.name
    if filename in BLOCKED_EXACT_FILES:
        raise SandboxSecurityError(
            f"Access to sensitive file '{filename}' is strictly blocked."
        )
    if filename.startswith(".env") and filename != ".env.example":
        raise SandboxSecurityError(
            f"Access to environment secret file '{filename}' is strictly blocked."
        )

    return candidate


def validate_file_extension(path: Path) -> None:
    """Validates that the file has an approved extension."""
    if path.name == ".env.example":
        return
    suffix = path.suffix.lower()
    if not suffix or suffix not in ALLOWED_EXTENSIONS:
        raise SandboxSecurityError(
            f"File extension '{suffix or 'none'}' is not in the allowed inspection list: {sorted(ALLOWED_EXTENSIONS)}"
        )
