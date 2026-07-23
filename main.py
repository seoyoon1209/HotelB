from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import dbpool
from ml import predictor
from router.HotelRouter import router as HotelRouter
from router.CustomerRouter import router as CustomerRouter
from router.RoomTypeRouter import router as RoomTypeRouter
from router.ReservationRouter import router as ReservationRouter
from router.PredictionRouter import router as PredictionRouter
from router.OverbookingRouter import router as OverbookingRouter
from router.ReservationActionRouter import router as ReservationActionRouter
from router.ReservationActionRouter import report_router as ActionReportRouter
from router.ModelInfoRouter import router as ModelInfoRouter
from router.AiInsightRouter import router as AiInsightRouter


@asynccontextmanager
async def lifespan(app: FastAPI):
    await dbpool.init()
    print("DB 실행")
    predictor.load_model()
    print("AI 모델 로드 완료")
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
app.include_router(ModelInfoRouter, prefix="/api")
app.include_router(AiInsightRouter, prefix="/api")


@app.get("/")
async def root():
    return {"message": "Hotel Reservation Cancellation Prediction API"}
