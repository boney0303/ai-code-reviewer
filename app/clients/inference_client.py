import os

import requests

from app.core.config import INFERENCE_TOKEN, INFERENCE_URL


def run_inference(prompt: str):
    payload = {
        "model": os.getenv("INFERENCE_MODEL", "example-code-review-model"),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 300,
    }

    headers = {
        "Authorization": f"Bearer {INFERENCE_TOKEN}",
        "Content-Type": "application/json",
    }

    r = requests.post(INFERENCE_URL, headers=headers, json=payload, timeout=(10, 180))
    return r.json()
