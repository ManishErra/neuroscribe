from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession

from database import get_db
from models import Session as SessionModel, Transcript, Note

import uuid
from datetime import date
import json

router = APIRouter(prefix="/sessions")


# GET all sessions for a patient
@router.get("/patient/{patient_id}")
def get_patient_sessions(
    patient_id: str,
    db: DBSession = Depends(get_db)
):
    sessions = db.query(SessionModel).filter(
        SessionModel.patient_id == patient_id
    ).order_by(SessionModel.session_date.desc()).all()

    result = []

    for s in sessions:

        note = db.query(Note).filter(
            Note.session_id == s.id
        ).first()

        result.append({
            "id": str(s.id),
            "session_date": str(s.session_date),
            "has_note": note is not None,
            "note_finalized": note.is_finalized if note else False
        })

    return result


# GET single session
@router.get("/{session_id}")
def get_session(
    session_id: str,
    db: DBSession = Depends(get_db)
):
    s = db.query(SessionModel).filter(
        SessionModel.id == session_id
    ).first()

    if not s:
        raise HTTPException(404, "Session not found")

    transcript = db.query(Transcript).filter(
        Transcript.session_id == session_id
    ).first()

    note = db.query(Note).filter(
        Note.session_id == session_id
    ).first()

    return {
        "id": str(s.id),
        "session_date": str(s.session_date),
        "transcript": transcript.raw_text if transcript else None,
        "note": json.loads(note.doctor_edited)
            if (note and note.doctor_edited)
            else None,
        "note_finalized": note.is_finalized if note else False
    }


# POST create session
class SessionCreate(BaseModel):
    patient_id: str


@router.post("/")
def create_session(
    data: SessionCreate,
    db: DBSession = Depends(get_db)
):

    session = SessionModel(
    id=uuid.uuid4(),
    patient_id=data.patient_id,
    session_date=date.today()
)

    db.add(session)
    db.commit()
    db.refresh(session)

    return {
        "id": str(session.id)
    }