import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.config import get_settings
from app.utils.db_pool import create_pool

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    if settings.LLM_CHAT_ONLY:
        app.state.pool = None
        logger.info("Mode chat-only aktif. Koneksi database dilewati.")
    else:
        app.state.pool = await create_pool()
        logger.info("Pool koneksi asyncpg aktif (min=%s, max=%s).", settings.POOL_MIN_SIZE, settings.POOL_MAX_SIZE)
    try:
        yield
    finally:
        if app.state.pool is not None:
            await app.state.pool.close()
            logger.info("Pool koneksi asyncpg ditutup.")


app = FastAPI(
    title="JXB Text-to-SQL Middleware",
    description="Middleware asinkron penerjemah pertanyaan pariwisata/perhotelan menjadi SQL analitik.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router, prefix="/api", tags=["text2sql"])