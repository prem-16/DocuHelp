"""Report endpoints (stub)"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/report/{report_id}")
def get_report(report_id: str):
    return {"report_id": report_id}
