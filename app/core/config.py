import os
from dotenv import load_dotenv
load_dotenv()

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
INFERENCE_TOKEN = os.environ["INFERENCE_TOKEN"]

GITHUB_API = os.getenv("GITHUB_API_URL", "https://github.example.com/api/v3")
INFERENCE_URL = os.getenv("INFERENCE_URL", "https://inference.example.com/v1/chat/completions")
