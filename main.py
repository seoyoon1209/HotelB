from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import dbpool
from router.HotelRouter import router as HotelRouter
from router.CustomerRouter import router as CustomerRouter
from router.RoomTypeRouter import router as RoomTypeRouter
from router.ReservationRouter import router as ReservationRouter
from router.PredictionRouter import router as PredictionRouter
from router.OverbookingRouter import router as OverbookingRouter
from router.ReservationActionRouter import router as ReservationActionRouter
from router.ReservationActionRouter import report_router as ActionReportRouter
from router.ReservationActionRouter import export_router as ActionExportRouter
from router.ModelInfoRouter import router as ModelInfoRouter
from router.AiInsightRouter import router as AiInsightRouter


@asynccontextmanager
async def lifespan(app: FastAPI):
    await dbpool.init()
    print("DB 실행")
    # 예측 모델은 메모리를 많이 써서(TF) 시작 시점에 로드하지 않고, 첫 예측 요청 때 지연 로드한다.
    print("서버 준비 완료 (모델은 첫 예측 요청 시 로드)")
    yield
    await dbpool.dispose()
    print("DB 종료")


app = FastAPI(title="Hotel Reservation Cancellation Prediction API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://smsf-0pzo.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(HotelRouter, prefix="/api")
app.include_router(CustomerRouter, prefix="/api")
app.include_router(RoomTypeRouter, prefix="/api")
app.include_router(ReservationRouter, prefix="/api")
app.include_router(PredictionRouter, prefix="/api")
app.include_router(OverbookingRouter, prefix="/api")
app.include_router(ReservationActionRouter, prefix="/api")
app.include_router(ActionReportRouter, prefix="/api")
app.include_router(ActionExportRouter, prefix="/api")
app.include_router(ModelInfoRouter, prefix="/api")
app.include_router(AiInsightRouter, prefix="/api")


@app.get("/")
async def root():
    return {"message": "Hotel Reservation Cancellation Prediction API"}
