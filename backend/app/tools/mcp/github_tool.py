import os
import base64
import httpx
from typing import Dict, Any, Optional
from backend.app.config import settings

SENSITIVE_FILENAMES = {".env", "id_rsa", "id_ed25519", "credentials.json", "service_account.json"}
MAX_FILE_BYTES = 500 * 1024  # 500KB


class GitHubTool:
    """
    MCP GitHub tool suite.
    - Read operations: open repositories or authenticated via GITHUB_TOKEN
    - Write operations: requires human approval
    - Push/Deploy: locked until Phase 11
    """

    @staticmethod
    def _get_headers() -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Rayhan-AI-Workbench/1.0",
        }
        token = os.getenv("GITHUB_TOKEN")
        if token and token != "your-github-token-here":
            headers["Authorization"] = f"Bearer {token}"
        return headers

    @classmethod
    async def read_file(cls, repo: str, path: str, branch: str = "main") -> Dict[str, Any]:
        # Sensitive file blocklist
        filename = path.split("/")[-1].lower()
        if filename in SENSITIVE_FILENAMES or filename.startswith(".env"):
            return {
                "success": False,
                "error": f"Access to sensitive file '{path}' is strictly blocked by security policy.",
            }

        url = f"https://api.github.com/repos/{repo}/contents/{path}?ref={branch}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(url, headers=cls._get_headers())
                if resp.status_code == 404:
                    return {"success": False, "error": f"File '{path}' not found in repo '{repo}' on branch '{branch}'."}
                if resp.status_code == 403:
                    return {"success": False, "error": "GitHub API rate limit exceeded or token unauthorized."}
                resp.raise_for_status()

                data = resp.json()
                if isinstance(data, list):
                    return {"success": False, "error": f"Path '{path}' is a directory, not a file."}

                size = data.get("size", 0)
                if size > MAX_FILE_BYTES:
                    return {"success": False, "error": f"File size {size} bytes exceeds maximum allowed limit of {MAX_FILE_BYTES} bytes."}

                content = data.get("content", "")
                encoding = data.get("encoding", "")
                if encoding == "base64":
                    decoded = base64.b64decode(content).decode("utf-8", errors="replace")
                else:
                    decoded = content

                return {
                    "success": True,
                    "repo": repo,
                    "path": path,
                    "branch": branch,
                    "size_bytes": size,
                    "content": decoded,
                }
            except Exception as e:
                return {"success": False, "error": f"GitHub API request failed: {str(e)}"}

    @classmethod
    async def list_files(cls, repo: str, path: str = "", branch: str = "main") -> Dict[str, Any]:
        url = f"https://api.github.com/repos/{repo}/contents/{path}?ref={branch}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(url, headers=cls._get_headers())
                if resp.status_code == 404:
                    return {"success": False, "error": f"Path '{path}' not found in '{repo}'."}
                resp.raise_for_status()

                items = resp.json()
                if not isinstance(items, list):
                    items = [items]

                files = [
                    {
                        "name": item.get("name"),
                        "path": item.get("path"),
                        "type": item.get("type"),
                        "size": item.get("size", 0),
                    }
                    for item in items
                ]
                return {"success": True, "repo": repo, "path": path, "count": len(files), "files": files}
            except Exception as e:
                return {"success": False, "error": f"GitHub list files failed: {str(e)}"}

    @classmethod
    async def read_pr(cls, repo: str, pr_number: int) -> Dict[str, Any]:
        url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(url, headers=cls._get_headers())
                if resp.status_code == 404:
                    return {"success": False, "error": f"PR #{pr_number} not found in '{repo}'."}
                resp.raise_for_status()

                data = resp.json()
                return {
                    "success": True,
                    "repo": repo,
                    "pr_number": pr_number,
                    "title": data.get("title"),
                    "state": data.get("state"),
                    "user": data.get("user", {}).get("login"),
                    "body": data.get("body", "")[:2000],
                    "changed_files": data.get("changed_files", 0),
                    "additions": data.get("additions", 0),
                    "deletions": data.get("deletions", 0),
                }
            except Exception as e:
                return {"success": False, "error": f"GitHub read PR failed: {str(e)}"}

    @classmethod
    async def list_issues(cls, repo: str, state: str = "open") -> Dict[str, Any]:
        url = f"https://api.github.com/repos/{repo}/issues?state={state}&per_page=15"
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(url, headers=cls._get_headers())
                resp.raise_for_status()
                data = resp.json()

                issues = [
                    {
                        "number": item.get("number"),
                        "title": item.get("title"),
                        "state": item.get("state"),
                        "author": item.get("user", {}).get("login"),
                        "created_at": item.get("created_at"),
                        "labels": [lbl.get("name") for lbl in item.get("labels", [])],
                    }
                    for item in data
                    if "pull_request" not in item  # filter out PRs
                ]
                return {"success": True, "repo": repo, "count": len(issues), "issues": issues}
            except Exception as e:
                return {"success": False, "error": f"GitHub list issues failed: {str(e)}"}

    @classmethod
    async def create_issue(cls, repo: str, title: str, body: str, labels: Optional[list] = None) -> Dict[str, Any]:
        url = f"https://api.github.com/repos/{repo}/issues"
        payload = {"title": title, "body": body}
        if labels:
            payload["labels"] = labels

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.post(url, headers=cls._get_headers(), json=payload)
                if resp.status_code == 401:
                    return {"success": False, "error": "GITHUB_TOKEN required with 'repo' scope to create issues."}
                resp.raise_for_status()
                data = resp.json()
                return {
                    "success": True,
                    "repo": repo,
                    "issue_number": data.get("number"),
                    "url": data.get("html_url"),
                    "title": data.get("title"),
                }
            except Exception as e:
                return {"success": False, "error": f"GitHub issue creation failed: {str(e)}"}

    @classmethod
    async def comment_pr(cls, repo: str, pr_number: int, comment: str) -> Dict[str, Any]:
        url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
        payload = {"body": comment}

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.post(url, headers=cls._get_headers(), json=payload)
                if resp.status_code == 401:
                    return {"success": False, "error": "GITHUB_TOKEN required to comment on PRs."}
                resp.raise_for_status()
                data = resp.json()
                return {
                    "success": True,
                    "repo": repo,
                    "pr_number": pr_number,
                    "comment_id": data.get("id"),
                    "url": data.get("html_url"),
                }
            except Exception as e:
                return {"success": False, "error": f"GitHub PR comment failed: {str(e)}"}
