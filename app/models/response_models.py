from typing import List, Dict, Any, Optional
from pydantic import BaseModel,Field


class ReviewComment(BaseModel):
    path: str
    line: int
    side: str = "RIGHT"
    body: str


class ReviewResponse(BaseModel):
    owner: str
    repo: str
    pull_number: int
    head_sha: Optional[str] = None
    reviewed_files: List[str] = Field(default_factory=list)
    skipped_files: List[str] = Field(default_factory=list)
    comments: List[ReviewComment] = Field(default_factory=list)
    comment_count: int = 0


class OrgReviewResponse(BaseModel):
    org: str
    total_prs: int
    results: List[Dict[str, Any]]