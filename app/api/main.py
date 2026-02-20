from fastapi import FastAPI
from app.api.routers import jobs
from prometheus_fastapi_instrumentator import Instrumentator
from app.db.database import engine, Base

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AUTOAPPLY-OPS API", version="1.0.0")

# Include routers
app.include_router(jobs.router, prefix="/api/v1", tags=["jobs"])

# Instrumentation
Instrumentator().instrument(app).expose(app)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"message": "Welcome to AutoApply Ops API"}
