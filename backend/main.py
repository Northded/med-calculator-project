from fastapi import FastAPI
from contextlib import asynccontextmanager

from backend.database.db import create_db


@asynccontextmanager
async def lifespan():
    await create_db()
    print("ON")
    yield
    print("OFF")


app = FastAPI(
    lifespan=lifespan,
    title="Медицинский Калькулятор",
    description="API для расчётов медицинских показателей",
)