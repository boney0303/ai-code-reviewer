from fastapi import APIRouter, HTTPException

from app.models.request_models import PRReviewRequest
from app.models.response_models import ReviewResponse
from app.services.review_service import review_pr

router = APIRouter()


@router.post("/pr", response_model=ReviewResponse)
def review_pr_api(req: PRReviewRequest):
    try:
        return review_pr(req.owner, req.repo, req.pull_number, req.post_comments)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))