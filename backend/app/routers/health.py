from typing import Any, Dict
from fastapi import APIRouter
from app.core.config import settings
from app.database.connection import check_database_connection

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check() -> Dict[str, Any]:
    """Basic health check endpoint returning system status and database connectivity."""
    db_connected, db_message = check_database_connection()

    return {
        "status": "healthy" if db_connected else "degraded",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": {
            "connected": db_connected,
            "message": db_message if (settings.DEBUG or db_connected) else "Database connection status masked",
        },
    }
