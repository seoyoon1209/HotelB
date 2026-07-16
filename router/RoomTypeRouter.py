# room_type 테이블 관련 API. 지금은 목록 조회만 있음.
# 호텔별 객실 유형 등록/수정, hotel_id로 필터링하는 조회 등을 여기에 추가.
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
