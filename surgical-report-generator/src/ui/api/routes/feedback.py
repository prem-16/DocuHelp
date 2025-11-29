"""Feedback endpoints (stub)"""

from fastapi import APIRouter

router = APIRouter()


@router.post("/feedback")
def post_feedback(payload: dict):
    return {"status": "received"}
