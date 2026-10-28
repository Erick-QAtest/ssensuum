from typing import Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import CustomerCreate, CustomerUpdate
from ..serializers import customer_payload, customer_profile_payload
from ..domain.customer_import import MAX_FILE_BYTES
from ..services import customer_import as import_service
from ..services import customers as customers_service

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("")
def search_customers(
    query: Optional[str] = Query(default=None, alias="q"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    stage: Optional[str] = Query(default=None),
    source: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> list[dict]:
    return [{**customer_payload(row), **summary} for row, summary in customers_service.search_customers(db, query, limit, offset, stage, source)]


@router.get("/funnel")
def funnel_summary(source: Optional[str] = Query(default=None), db: Session = Depends(get_db)) -> dict:
    return customers_service.funnel_summary(db, source)


@router.post("", status_code=201)
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)) -> dict:
    return customer_payload(customers_service.create_customer(db, payload))


@router.post("/import")
def import_customers(
    file: UploadFile = File(...),
    dry_run: bool = Query(default=True, alias="dryRun"),
    db: Session = Depends(get_db),
) -> dict:
    # Se lee un byte de más para detectar archivos que exceden el límite sin cargarlos completos.
    content = file.file.read(MAX_FILE_BYTES + 1)
    return import_service.import_customers(db, file.filename or "", content, dry_run)


@router.get("/{customer_id}")
def get_customer(customer_id: str, db: Session = Depends(get_db)) -> dict:
    return customer_payload(customers_service.get_customer(db, customer_id))


@router.get("/{customer_id}/profile")
def customer_profile(customer_id: str, db: Session = Depends(get_db)) -> dict:
    return customer_profile_payload(*customers_service.customer_profile(db, customer_id))


@router.patch("/{customer_id}")
def update_customer(customer_id: str, payload: CustomerUpdate, db: Session = Depends(get_db)) -> dict:
    return customer_payload(customers_service.update_customer(db, customer_id, payload))
