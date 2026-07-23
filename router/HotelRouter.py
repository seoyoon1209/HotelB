# hotel 테이블
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from db.dbpool import DbPoolDep

router = APIRouter(prefix="/hotels", tags=["hotels"])


class HotelResponse(BaseModel):
    hotel_id: int
    hotel_name: str
    hotel_type: str | None = None
    city: str | None = None
    country: str | None = None


@router.get("/", response_model=list[HotelResponse])
async def list_hotels(conn: DbPoolDep):
    rows = await conn.fetch("SELECT * FROM hotel ORDER BY hotel_id")
    return [dict(row) for row in rows]
