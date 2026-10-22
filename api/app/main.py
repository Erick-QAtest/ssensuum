from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .db import Base, SessionLocal, add_missing_columns, engine
from .domain.errors import DomainError
from .routers import admin, availability, catalog, checkout, customers, events, finance, health, hr, records, reservations
from .seed import seed


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    add_missing_columns()
    with SessionLocal() as db:
        seed(db)
    yield


app = FastAPI(title="SSENSUUM API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(DomainError)
async def domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


app.include_router(health.router)
app.include_router(catalog.router)
app.include_router(availability.router)
app.include_router(reservations.router)
app.include_router(customers.router)
app.include_router(admin.router)
app.include_router(checkout.router)
app.include_router(events.router)
app.include_router(records.router)
app.include_router(hr.router)
app.include_router(finance.router)
