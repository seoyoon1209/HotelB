# customer 테이블 관련 (추후 고객 등록/수정, 단건 조회, 이메일 중복 체크)
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from db.dbpool import DbPoolDep

router = APIRouter(prefix="/customers", tags=["customers"])


class CustomerResponse(BaseModel):
    customer_id: int
    customer_name: str | None = None
    email: str | None = None
    phone: str | None = None
    country: str | None = None


@router.get("/", response_model=list[CustomerResponse])
async def list_customers(conn: DbPoolDep):
    rows = await conn.fetch("SELECT * FROM customer ORDER BY customer_id")
    return [dict(row) for row in rows]
