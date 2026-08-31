from fastapi import FastAPI
from app.api.review import router as review_router

app = FastAPI(title="AI Code Reviewer", version="1.0.0")

app.include_router(review_router, prefix="/review", tags=["review"])


@app.get("/health")
def health():
    return {"status": "ok"}
