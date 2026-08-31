import logging
import re
from pathlib import Path
from app.core.constants import NODEJS_PROMPT, PYTHON_PROMPT, K8S_PROMPT, DEFAULT_PROMPT, MAX_FILE_CONTEXT_CHARS, MAX_PATCH_CHARS, SUPPORTED_EXTENSIONS, NON_K8S_PATH_HINTS, NON_K8S_YAML_NAMES, K8S_PATH_HINTS, K8S_KINDS
logger = logging.getLogger(__name__)

def is_supported_file(filename: str) -> bool:
    return filename.lower().endswith(SUPPORTED_EXTENSIONS)

def looks_like_k8s_yaml(filename: str, patch: str = "", file_content: str = "") -> bool:
    lower = filename.lower()
    base = Path(lower).name

    if base in NON_K8S_YAML_NAMES:
        return False

    if any(hint in lower for hint in NON_K8S_PATH_HINTS):
        return False

    if any(hint in lower for hint in K8S_PATH_HINTS):
        return True

    sample = "\n".join([patch or "", file_content or ""])[:MAX_FILE_CONTEXT_CHARS].lower()

    api_version = re.search(r"(?m)^\s*apiVersion\s*:\s*\S+", sample, re.IGNORECASE)
    kind_match = re.search(r"(?m)^\s*kind\s*:\s*([A-Za-z0-9]+)\s*$", sample, re.IGNORECASE)
    if not api_version or not kind_match:
        return False

    kind = kind_match.group(1).lower()
    return kind in K8S_KINDS

def get_profile(filename: str, patch: str = "", file_content: str = "") -> str:
    lower = filename.lower()

    if lower.endswith((".js", ".jsx", ".ts", ".tsx")):
        return "node"

    if lower.endswith(".py"):
        return "python"

    if lower.endswith((".yml", ".yaml")):
        return "k8s" if looks_like_k8s_yaml(filename, patch=patch, file_content=file_content) else "default"

    return "default"


def build_prompt(filename: str, patch: str, max_comments: int, file_content: str = "", profile: str = "default") -> str:
    base = {
        "node": NODEJS_PROMPT,
        "python": PYTHON_PROMPT,
        "k8s": K8S_PROMPT,
    }.get(profile, DEFAULT_PROMPT)

    prompt = base.replace("__MAX_COMMENTS__", str(max_comments))

    prompt += (
        "\n\nIMPORTANT REVIEW RULES:\n"
        "- Use file context when available.\n"
        "- Focus on issues introduced by the diff or directly affected by it.\n"
        "- Do not comment on unrelated existing code.\n"
        "- Prefer concrete bugs, regressions, validation issues, security issues, and missing error handling.\n"
        "- Return only valid JSON.\n"
    )

    prompt += f"\nFILE: {filename}\nPROFILE: {profile}\n"

    if file_content:
        prompt += "\nFULL FILE CONTEXT:\n"
        prompt += file_content[:MAX_FILE_CONTEXT_CHARS]
        prompt += "\n"

    prompt += "\nDIFF:\n"
    prompt += patch[:MAX_PATCH_CHARS]

    return prompt

