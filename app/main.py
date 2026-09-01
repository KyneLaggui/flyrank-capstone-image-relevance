from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.images import router as images_router
from app.api.posts import router as posts_router
from app.db import engine


app = FastAPI(
    title="AI Image Understanding & Content Matching Engine",
    version="0.1.0",
)


app.include_router(images_router)
app.include_router(posts_router)


@app.get("/health")
def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "database": "connected",
        }

    except SQLAlchemyError:
        return {
            "status": "error",
            "database": "disconnected",
        }
