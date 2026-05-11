from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, ValidationError
from groq import Groq
from sqlalchemy.orm import Session as DBSession

from database import get_db
from models import Note, Transcript
from prompts import (
    SYSTEM_PROMPT,
    build_user_prompt,
    safety_filter
)

from typing import List

import os
import uuid
import json
import re

from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

# =========================
# REQUEST MODELS
# =========================

class NoteRequest(BaseModel):

    transcript_id: str

    patient_name: str

    patient_age: int


class ClinicalNoteSchema(BaseModel):

    presenting_complaint: str

    symptoms_mentioned: List[str]

    medications_mentioned: List[str]

    sleep: str

    mood_in_patient_words: str

    social_context: str

    plan_discussed: str

    flags_for_review: str

    confidence: str


class SaveNoteRequest(BaseModel):

    note_id: str

    doctor_edited: ClinicalNoteSchema


# =========================
# CLEAN LLM JSON
# =========================

def clean_llm_json(text: str) -> str:

    text = text.strip()

    # Remove markdown code fences
    text = re.sub(r"^```json", "", text)
    text = re.sub(r"^```", "", text)
    text = re.sub(r"```$", "", text)

    return text.strip()


# =========================
# GENERATE AI NOTE
# =========================

@router.post("/generate-note")
def generate_note(
    req: NoteRequest,
    db: DBSession = Depends(get_db)
):

    # =========================
    # FETCH TRANSCRIPT
    # =========================

    transcript = db.query(Transcript).filter(
        Transcript.id == req.transcript_id
    ).first()

    if not transcript:

        raise HTTPException(
            status_code=404,
            detail="Transcript not found"
        )

    # =========================
    # VALIDATE TRANSCRIPT
    # =========================

    if not transcript.raw_text:

        raise HTTPException(
            status_code=400,
            detail="Transcript is empty"
        )

    # =========================
    # CALL LLM
    # =========================

    try:

        response = client.chat.completions.create(

            model="llama-3.3-70b-versatile",

            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": build_user_prompt(
                        transcript.raw_text,
                        req.patient_name,
                        req.patient_age
                    )
                }
            ],

            temperature=0.2,
            max_tokens=1000
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"LLM call failed: {str(e)}"
        )

    # =========================
    # EXTRACT OUTPUT
    # =========================

    raw_output = response.choices[0].message.content

    if not raw_output or not raw_output.strip():

        raise HTTPException(
            status_code=500,
            detail="LLM returned empty response"
        )

    # =========================
    # SAFETY FILTER
    # =========================

    filtered_output, flagged = safety_filter(raw_output)

    # =========================
    # CLEAN JSON
    # =========================

    filtered_output = clean_llm_json(filtered_output)

    # =========================
    # PARSE JSON
    # =========================

    try:

        parsed_json = json.loads(filtered_output)

    except json.JSONDecodeError:

        raise HTTPException(
            status_code=500,
            detail="LLM returned invalid JSON"
        )

    # =========================
    # VALIDATE AI STRUCTURE
    # =========================

    try:

        validated_note = ClinicalNoteSchema(
            **parsed_json
        )

    except ValidationError as e:

        raise HTTPException(
            status_code=500,
            detail=f"AI note schema invalid: {str(e)}"
        )

    # =========================
    # SAVE AI DRAFT
    # =========================

    note = Note(

        id=uuid.uuid4(),

        session_id=transcript.session_id,

        ai_draft=json.dumps(
            validated_note.model_dump()
        ),

        is_finalized=False
    )

    db.add(note)

    db.commit()

    db.refresh(note)

    return {
        "note_id": str(note.id),

        "ai_draft": validated_note.model_dump(),

        "flagged_phrases": flagged
    }


# =========================
# SAVE DOCTOR REVIEWED NOTE
# =========================

@router.post("/save-note")
def save_note(
    req: SaveNoteRequest,
    db: DBSession = Depends(get_db)
):

    # =========================
    # FETCH NOTE
    # =========================

    note = db.query(Note).filter(
        Note.id == req.note_id
    ).first()

    if not note:

        raise HTTPException(
            status_code=404,
            detail="Note not found"
        )

    # =========================
    # PREVENT DOUBLE FINALIZE
    # =========================

    if note.is_finalized:

        raise HTTPException(
            status_code=400,
            detail="Note already finalized"
        )

    # =========================
    # EMPTY VALIDATION
    # =========================

    note_values = (
        req.doctor_edited
        .model_dump()
        .values()
    )

    if not any(
        str(v).strip()
        for v in note_values
    ):

        raise HTTPException(
            status_code=400,
            detail="Cannot save empty note"
        )

    # =========================
    # SAVE FINAL NOTE
    # =========================

    note.doctor_edited = json.dumps(
        req.doctor_edited.model_dump()
    )

    note.is_finalized = True

    db.commit()

    return {

        "status": "saved",

        "note_id": req.note_id
    }