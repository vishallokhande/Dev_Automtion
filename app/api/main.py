from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api.routers import jobs, auth
from prometheus_fastapi_instrumentator import Instrumentator
from app.db.database import engine, Base
from app.db.user_models import UserModel, UserProfileModel
from app.db.models import JobModel

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AUTOAPPLY-OPS API", version="1.0.0")

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(jobs.router, prefix="/api/v1", tags=["jobs"])

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Instrumentation
Instrumentator().instrument(app).expose(app)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/")
async def root():
    return FileResponse("app/static/index.html")
