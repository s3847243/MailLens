from fastapi import APIRouter

from ..schemas import HealthOut

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", response_model=HealthOut)
def healthcheck():
    return {"status": "ok"}
