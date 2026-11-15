from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import FeedbackCreate
from ..serializers import feedback_payload
from ..services import feedback as feedback_service

# Público: el id del servicio registrado es imposible de adivinar y solo llega al cliente por SMS.
router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.get("/{visit_id}")
def feedback_context(visit_id: str, db: Session = Depends(get_db)) -> dict:
    return feedback_service.feedback_context(db, visit_id)


@router.post("/{visit_id}", status_code=201)
def submit_feedback(visit_id: str, payload: FeedbackCreate, db: Session = Depends(get_db)) -> dict:
    return feedback_payload(feedback_service.submit_feedback(db, visit_id, payload))
