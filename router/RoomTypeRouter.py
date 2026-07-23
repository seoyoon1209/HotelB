# 호텔별 객실 유형 등록/수정
from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter
from pydantic import BaseModel
from db.dbpool import DbPoolDep

router = APIRouter(prefix="/room-types", tags=["room-types"])


class RoomTypeResponse(BaseModel):
    room_type_id: int
    hotel_id: int
    room_type_code: str
    room_type_name: str
    capacity: int | None = None
    base_price: Decimal | None = None


@router.get("/", response_model=list[RoomTypeResponse])
async def list_room_types(conn: DbPoolDep):
    rows = await conn.fetch("SELECT * FROM room_type ORDER BY room_type_id")
    return [dict(row) for row in rows]
