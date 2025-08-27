from fastapi import Depends

from .db import get_db


def db_dep(db=Depends(get_db)):
    return db
