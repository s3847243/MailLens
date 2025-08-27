from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from .. import models
from ..db import get_db
from ..utils.jwt import get_user_id_from_cookie

router = APIRouter(prefix="/me", tags=["auth"])


@router.get("")
async def me(request: Request, db: Session = Depends(get_db)):
    user_id = get_user_id_from_cookie(request)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Not authenticated")
    user = db.query(models.User).filter(
        models.User.id == user_id).one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="User not found")
    return {"id": str(user.id), "email": user.email, "name": user.name, "picture_url": user.picture_url}
