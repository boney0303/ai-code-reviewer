from typing import List, Dict, Any, Optional
from app.clients.github_client import get_pr_info, get_pr_files


def fetch_pr_context(owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
    pr = get_pr_info(owner, repo, pr_number)
    files = get_pr_files(owner, repo, pr_number)

    return {
        "owner": owner,
        "repo": repo,
        "pr_number": pr_number,
        "head_sha": pr["head"]["sha"],
        "base_sha": pr["base"]["sha"],
        "title": pr.get("title", ""),
        "author": pr.get("user", {}).get("login", ""),
        "html_url": pr.get("html_url", ""),
        "files": files,
    }


def extract_reviewable_files(files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    reviewable = []

    for f in files:
        filename = f.get("filename", "")
        patch = f.get("patch")

        if not patch:
            continue

        reviewable.append({
            "filename": filename,
            "patch": patch,
        })

    return reviewable


def extract_file_context(f: Dict[str, Any]) -> str:
    """
    Best-effort file snapshot for prompt context.
    The fetch_pr_context() function should ideally populate one of these keys.
    """
    for key in ("content", "contents", "file_content", "snapshot", "head_content"):
        value = f.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""

def _safe_line(value: Any) -> Optional[int]:
    try:
        line = int(value)
        return line if line > 0 else None
    except Exception:
        return None

def _normalize_model_comments(raw_comments: Any) -> List[Dict[str, Any]]:
    if not isinstance(raw_comments, list):
        return []

    out: List[Dict[str, Any]] = []
    seen = set()

    for c in raw_comments:
        if not isinstance(c, dict):
            continue

        line = _safe_line(c.get("line"))
        body = c.get("body")
        side = c.get("side", "RIGHT")

        if line is None or not isinstance(body, str) or not body.strip():
            continue

        if side not in ("RIGHT", "LEFT"):
            side = "RIGHT"

        body = body.strip()

        key = (line, side, body)
        if key in seen:
            continue
        seen.add(key)

        out.append({
            "line": line,
            "side": side,
            "body": body,
        })

    return out

