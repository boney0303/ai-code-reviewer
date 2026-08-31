import requests
from typing import List, Dict
from app.core.config import GITHUB_API, GITHUB_TOKEN
import json

headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
}


def get_pr_info(owner: str, repo: str, pr_number: int) -> Dict:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}"
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()

def get_pr_files(owner: str, repo: str, pr_number: int) -> List[Dict]:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}/files"
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()

def post_comment(owner, repo, pr_number, payload):
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}/comments"
    r = requests.post(url, headers=headers, timeout=30, data=json.dumps(payload))
    r.raise_for_status()
    return r.json()