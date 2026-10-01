"""
P_311 Knowledge-Driven IoT Fault Diagnosis Assistant
Main FastAPI Application Entrypoint with Lifespan Lifecycle Management.
"""
import asyncio
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes import router
from backend.app.core.config import settings
from backend.app.db.database import db_manager
from backend.app.mqtt.consumer import mqtt_service
from backend.app.rag.knowledge_indexer import knowledge_indexer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up P_311 Backend Service...")

    # 1. Initialize SQLite tables and machine records
    await db_manager.init_db()

    # 2. Check / Pre-warm vector index
    if len(knowledge_indexer.chunks) == 0:
        logger.info("Ingesting technical manuals into vector store...")
        knowledge_indexer.ingest_all()

    # 3. Bind asyncio loop and start MQTT consumer
    loop = asyncio.get_running_loop()
    mqtt_service.set_event_loop(loop)
    mqtt_service.start()

    logger.info("P_311 Backend ready on port 8000. OpenAPI docs at /docs")
    yield

    logger.info("Shutting down P_311 Backend Service...")
    mqtt_service.stop()
    await db_manager.close()


app = FastAPI(
    title="P_311 IoT Fault Diagnosis Assistant",
    description="Knowledge-driven real-time IoT telemetry monitoring, deterministic fault detection, and local LLM/RAG diagnosis.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for React / Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes under both /api and root for compatibility
app.include_router(router, prefix="/api")
app.include_router(router)

# Mount frontend build if available
from fastapi.staticfiles import StaticFiles
dist_dir = settings.BASE_DIR / "frontend" / "dist"
if dist_dir.exists():
    app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
