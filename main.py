from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import dbpool
from router.HotelRouter import router as HotelRouter
from router.CustomerRouter import router as CustomerRouter
from router.RoomTypeRouter import router as RoomTypeRouter
from router.ReservationRouter import router as ReservationRouter
from router.PredictionRouter import router as PredictionRouter


@asynccontextmanager
async def lifespan(app: FastAPI):
    await dbpool.init()
    print("DB 실행")
    yield
    await dbpool.dispose()
    print("DB 종료")


app = FastAPI(title="Hotel Reservation Cancellation Prediction API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(HotelRouter, prefix="/api")
app.include_router(CustomerRouter, prefix="/api")
app.include_router(RoomTypeRouter, prefix="/api")
app.include_router(ReservationRouter, prefix="/api")
app.include_router(PredictionRouter, prefix="/api")


@app.get("/")
async def root():
    return {"message": "Hotel Reservation Cancellation Prediction API"}
