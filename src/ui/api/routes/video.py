"""Video endpoints (stub)"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/video/{video_id}")
def get_video(video_id: str):
    return {"video_id": video_id}
