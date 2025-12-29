from fastapi import FastAPI
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan():
    ...


app = FastAPI(
    lifespan=lifespan,
    title="Медицинский Калькулятор",
    description="API для расчётов медицинских показателей",
)