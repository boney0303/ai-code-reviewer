from typing import Optional
from pydantic import BaseModel, Field


class PRReviewRequest(BaseModel):
    owner: str = Field(..., examples=["example-org"])
    repo: str = Field(..., examples=["example-service"])
    pull_number: int = Field(..., ge=1)
    post_comments: bool = True


class OrgReviewRequest(BaseModel):
    org: str = Field(..., examples=["example-org"])
    post_comments: bool = True
    repo_prefix: Optional[str] = None
    max_workers: int = 10


class WebhookReviewRequest(BaseModel):
    org: str
    repo: str
    pull_number: int
    action: str
    head_sha: Optional[str] = None
