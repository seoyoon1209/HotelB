# customer 테이블 관련 API. 지금은 목록 조회만 있음.
# 추후 고객 등록/수정, 단건 조회, 이메일 중복 체크 등을 여기에 추가.
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
