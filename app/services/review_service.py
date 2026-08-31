import json
from typing import Any, Dict, List

from app.services.pr_service import fetch_pr_context, extract_reviewable_files, _normalize_model_comments, extract_file_context
from app.services.prompt_service import build_prompt, is_supported_file, get_profile
from app.clients.inference_client import run_inference
from app.clients.github_client import post_comment
from app.utils.logger import get_logger
from app.core.constants import MAX_COMMENTS

logger = get_logger(__name__)


def review_pr(owner: str, repo: str, pr_number: int, post_comments: bool = True) -> Dict[str, Any]:
    """
    Main PR review function
    """
    logger.info("Starting review for %s/%s PR #%s", owner, repo, pr_number)

    context = fetch_pr_context(owner, repo, pr_number)
    files = context.get("files", [])
    head_sha = context["head_sha"]

    all_comments: List[Dict[str, Any]] = []
    reviewed_files: List[str] = []
    skipped_files: List[str] = []
    seen_comments = set()

    for f in files:
        filename = f.get("filename")
        if not filename:
            continue

        if not is_supported_file(filename):
            skipped_files.append(filename)
            continue

        patch = f.get("patch") or ""
        if not patch.strip():
            skipped_files.append(filename)
            continue

        file_content = extract_file_context(f)
        profile = get_profile(filename, patch=patch, file_content=file_content)

        logger.info("Reviewing %s", filename)
        reviewed_files.append(filename)

        try:
            prompt = build_prompt(
                filename=filename,
                patch=patch,
                max_comments=MAX_COMMENTS,
                file_content=file_content,
                profile=profile
            )

            result = run_inference(prompt)

            content = result["choices"][0]["message"]["content"]

            try:
                parsed = json.loads(content)
            except Exception:
                logger.error("Invalid JSON from model for %s", filename)
                logger.debug("Raw model output for %s: %s", filename, content)
                continue

            comments = _normalize_model_comments(parsed.get("comments", []))

            for c in comments:
                comment_key = (filename, c["line"], c["side"], c["body"])
                if comment_key in seen_comments:
                    continue
                seen_comments.add(comment_key)

                comment_obj = {
                    "path": filename,
                    "line": c["line"],
                    "side": c.get("side", "RIGHT"),
                    "body": c["body"],
                }

                all_comments.append(comment_obj)

                if post_comments:
                    try:
                        payload = {
                            "body": f"{c['body']}\n\n---\n🤖 Automated review by AI Code Reviewer",
                            "commit_id": head_sha,
                            "path": filename,
                            "line": c["line"],
                            "side": c.get("side", "RIGHT"),
                        }

                        post_comment(owner, repo, pr_number, payload)
                        logger.info(
                            "Posted comment to %s:%s line %s",
                            filename,
                            c["line"],
                            c["side"],
                        )
                    except Exception as e:
                        logger.error("Failed to post comment for %s: %s", filename, e)

        except Exception as e:
            logger.error("Error reviewing %s: %s", filename, e)
            continue

    logger.info("Review completed for PR #%s with %s comments", pr_number, len(all_comments))

    return {
        "owner": owner,
        "repo": repo,
        "pull_number": pr_number,
        "head_sha": head_sha,
        "reviewed_files": reviewed_files,
        "skipped_files": skipped_files,
        "comment_count": len(all_comments),
        "comments": all_comments,
    }
