from fastapi import APIRouter
from app.database.influxdb import check_influxdb_connection


router = APIRouter()


@router.get("/health")
def health_check():
    database_status = check_influxdb_connection()

    return {
        "status": "healthy" if database_status else "unhealthy",
        "database": "connected" if database_status else "disconnected"
    }