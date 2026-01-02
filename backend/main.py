import time
import uvicorn
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.routes.calculations import router as calc_router
from backend.routes.health import router as health_router
from backend.database.db import create_db


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db()
    print("ON")
    yield
    print("OFF")


app = FastAPI(
    lifespan=lifespan,
    title="Медицинский Калькулятор",
    description="API для расчётов медицинских показателей",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    logger.info(f"{request.method} {request.url.path}")

    if request.query_params:
        logger.info(f"Query: {dict(request.query_params)}")

    response = await call_next(request)

    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.3f}"

    status = "V" if response.status_code < 400 else "X"
    logger.info(
        f"{status} {request.method} {request.url.path} - "
        f"Status: {response.status_code} | Time: {process_time:.3f}s"
    )

    return response


app.include_router(health_router, prefix="/api")
app.include_router(calc_router, prefix="/api")


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )