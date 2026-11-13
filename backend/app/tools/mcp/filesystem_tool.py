import os
import shutil
import difflib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional


class SandboxViolationError(Exception):
    """Raised when a filesystem operation attempts to escape sandbox or access sensitive files."""
    pass


ALLOWED_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".md", ".txt",
    ".yml", ".yaml", ".html", ".css", ".toml", ".sql", ".sh"
}
BLOCKED_EXACT_NAMES = {".env", "id_rsa", "id_ed25519", "credentials.json", "service_account.json"}
MAX_FILE_BYTES = 500 * 1024  # 500KB


class FilesystemTool:
    """
    Sandboxed MCP Filesystem tool.
    Strictly forbids path traversal and sensitive files.
    - fs_read_file
    - fs_list_directory
    - fs_write_file (creates backup and generates diff)
    - fs_delete_file (moves to .trash/ directory, never permanently deletes)
    """
    WORKSPACE_ROOT = Path("/app/applet").resolve()
    BACKUP_DIR = WORKSPACE_ROOT / ".workbench_backups"
    TRASH_DIR = WORKSPACE_ROOT / ".trash"

    @classmethod
    def _validate_path(cls, relative_path: str) -> Path:
        target = (cls.WORKSPACE_ROOT / relative_path.lstrip("/")).resolve()

        # Path traversal guard
        try:
            target.relative_to(cls.WORKSPACE_ROOT)
        except ValueError:
            raise SandboxViolationError(f"Path traversal blocked: '{relative_path}' resolves outside workspace.")

        # Blocked file names
        if target.name.lower() in BLOCKED_EXACT_NAMES or target.name.startswith(".env"):
            if not target.name.endswith(".example"):
                raise SandboxViolationError(f"Access to sensitive file '{target.name}' is strictly blocked.")

        return target

    @classmethod
    def read_file(cls, path: str) -> Dict[str, Any]:
        try:
            target = cls._validate_path(path)
            if not target.exists():
                return {"success": False, "error": f"File '{path}' does not exist."}
            if target.is_dir():
                return {"success": False, "error": f"Path '{path}' is a directory."}

            size = target.stat().st_size
            if size > MAX_FILE_BYTES:
                return {"success": False, "error": f"File size {size} exceeds limit of {MAX_FILE_BYTES} bytes."}

            with open(target, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            return {
                "success": True,
                "path": str(target.relative_to(cls.WORKSPACE_ROOT)),
                "size_bytes": size,
                "content": content,
            }
        except SandboxViolationError as sve:
            return {"success": False, "error": str(sve)}
        except Exception as e:
            return {"success": False, "error": f"Read error: {str(e)}"}

    @classmethod
    def list_directory(cls, path: str = ".", max_depth: int = 3) -> Dict[str, Any]:
        try:
            target = cls._validate_path(path)
            if not target.exists():
                return {"success": False, "error": f"Directory '{path}' does not exist."}
            if not target.is_dir():
                return {"success": False, "error": f"Path '{path}' is not a directory."}

            results: List[Dict[str, Any]] = []
            max_depth = min(max_depth, 5)

            for root, dirs, files in os.walk(target):
                dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "__pycache__", ".pytest_cache", ".trash", ".workbench_backups"}]
                rel_root = Path(root).relative_to(target)
                current_depth = len(rel_root.parts)
                if current_depth > max_depth:
                    continue

                for f in files:
                    file_path = Path(root) / f
                    if file_path.name.startswith(".env") and not file_path.name.endswith(".example"):
                        continue
                    results.append({
                        "name": f,
                        "path": str(file_path.relative_to(cls.WORKSPACE_ROOT)),
                        "type": "file",
                        "size": file_path.stat().st_size,
                    })

                for d in dirs:
                    dir_path = Path(root) / d
                    results.append({
                        "name": d,
                        "path": str(dir_path.relative_to(cls.WORKSPACE_ROOT)),
                        "type": "directory",
                    })

                if len(results) >= 200:
                    break

            return {
                "success": True,
                "path": path,
                "count": len(results),
                "entries": results[:200],
            }
        except SandboxViolationError as sve:
            return {"success": False, "error": str(sve)}
        except Exception as e:
            return {"success": False, "error": f"List error: {str(e)}"}

    @classmethod
    def generate_diff(cls, path: str, new_content: str) -> Dict[str, Any]:
        """Generates unified diff preview without applying change."""
        try:
            target = cls._validate_path(path)
            old_lines = []
            if target.exists() and target.is_file():
                with open(target, "r", encoding="utf-8", errors="replace") as f:
                    old_lines = f.readlines()

            new_lines = new_content.splitlines(keepends=True)
            diff = difflib.unified_diff(
                old_lines,
                new_lines,
                fromfile=f"a/{path}",
                tofile=f"b/{path}",
                lineterm="",
            )
            return {"success": True, "diff": "\n".join(diff)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def write_file(cls, path: str, content: str, reason: str = "") -> Dict[str, Any]:
        try:
            target = cls._validate_path(path)
            target.parent.mkdir(parents=True, exist_ok=True)

            # Automated backup if file exists
            if target.exists():
                cls.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                backup_file = cls.BACKUP_DIR / f"{target.name}.{timestamp}.bak"
                shutil.copy2(target, backup_file)

            with open(target, "w", encoding="utf-8") as f:
                f.write(content)

            return {
                "success": True,
                "path": str(target.relative_to(cls.WORKSPACE_ROOT)),
                "size_bytes": len(content.encode("utf-8")),
                "reason": reason,
            }
        except SandboxViolationError as sve:
            return {"success": False, "error": str(sve)}
        except Exception as e:
            return {"success": False, "error": f"Write error: {str(e)}"}

    @classmethod
    def delete_file(cls, path: str, reason: str = "") -> Dict[str, Any]:
        """
        Soft-delete only. Moves target file to .trash/ with timestamp.
        Never permanently unlinks.
        """
        try:
            target = cls._validate_path(path)
            if not target.exists():
                return {"success": False, "error": f"File '{path}' does not exist."}

            cls.TRASH_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            trash_target = cls.TRASH_DIR / f"{target.name}.{timestamp}.deleted"

            shutil.move(str(target), str(trash_target))

            return {
                "success": True,
                "path": str(target.relative_to(cls.WORKSPACE_ROOT)),
                "moved_to": str(trash_target.relative_to(cls.WORKSPACE_ROOT)),
                "reason": reason,
                "soft_delete": True,
            }
        except SandboxViolationError as sve:
            return {"success": False, "error": str(sve)}
        except Exception as e:
            return {"success": False, "error": f"Delete error: {str(e)}"}
