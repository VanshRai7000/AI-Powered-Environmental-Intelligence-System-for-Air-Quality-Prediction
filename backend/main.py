from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.routes.health import router as health_router
from app.routes.users import router as users_router
from app.routes.location import router as location_router
from app.routes.air_quality import router as air_quality_router
from app.routes.weather import router as weather_router
from app.routes.environmental import router as environmental_router

app = FastAPI(
    title="Environmental Intelligence API",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(users_router)
app.include_router(location_router)
app.include_router(air_quality_router)
app.include_router(weather_router)
app.include_router(environmental_router)


@app.get("/")
async def root():
    return {
        "message": "Environmental Intelligence API is running"
    }
