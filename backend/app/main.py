from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import (
    ai,
    analytics,
    audit_logs,
    auth,
    batch,
    customers,
    dashboard,
    export,
    orders,
    products,
    upload,
    users,
)

# Ensure all models are imported so Base.metadata knows about every table.
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create all database tables on startup if they do not already exist."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="InsightFlow API",
    description="Business intelligence and analytics platform backend.",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(dashboard.router)
app.include_router(orders.router)
app.include_router(customers.router)
app.include_router(products.router)
app.include_router(upload.router)
app.include_router(analytics.router)
app.include_router(ai.router)
app.include_router(export.router)
app.include_router(audit_logs.router)
app.include_router(batch.router)


# ---------------------------------------------------------------------------
# Root endpoint
# ---------------------------------------------------------------------------
@app.get("/", tags=["root"])
def root():
    """Health-check / root endpoint."""
    return {"message": "InsightFlow API", "version": "1.0.0"}
