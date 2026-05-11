from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from groq import Groq
from sqlalchemy.orm import Session as DBSession
from database import get_db
from models import Note, Transcript
from prompts import SYSTEM_PROMPT, build_user_prompt, safety_filter

import os
import uuid
import json

from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


class NoteRequest(BaseModel):
    transcript_id: str
    patient_name: str
    patient_age: int


@router.post("/generate-note")
def generate_note(
    req: NoteRequest,
    db: DBSession = Depends(get_db)
):

    # 1. Fetch transcript from DB
    transcript = db.query(Transcript).filter(
        Transcript.id == req.transcript_id
    ).first()

    if not transcript:
        raise HTTPException(
            status_code=404,
            detail="Transcript not found"
        )

    # 2. Call Groq LLM
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

    raw_output = response.choices[0].message.content

    # 3. Safety filter
    filtered_output, flagged = safety_filter(raw_output)

    # 4. Parse JSON
    try:
        note_data = json.loads(filtered_output)

    except json.JSONDecodeError:

        note_data = {
            "raw_response": filtered_output,
            "parse_error": "LLM did not return valid JSON"
        }

    # 5. Save AI draft
    note = Note(
        id=uuid.uuid4(),
        session_id=transcript.session_id,
        ai_draft=json.dumps(note_data),
        is_finalized=False
    )

    db.add(note)
    db.commit()
    db.refresh(note)

    return {
        "note_id": str(note.id),
        "ai_draft": note_data,
        "flagged_phrases": flagged
    }