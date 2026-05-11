from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    Depends,
    Form
)

from groq import Groq
from sqlalchemy.orm import Session as DBSession

from database import get_db
from models import Transcript, Session as SessionModel

import os
import uuid

from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

UPLOAD_DIR = "uploads"

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)

ALLOWED_TYPES = [
    "audio/mpeg",
    "audio/wav",
    "audio/mp4",
    "audio/x-m4a",
    "audio/webm"
]


@router.post("/upload-audio")
async def upload_audio(
    session_id: str = Form(...),
    file: UploadFile = File(...),
    db: DBSession = Depends(get_db)
):

    # =========================
    # Validate session exists
    # =========================

    existing_session = db.query(SessionModel).filter(
        SessionModel.id == session_id
    ).first()

    if not existing_session:

        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    # =========================
    # Validate file type
    # =========================

    if file.content_type not in ALLOWED_TYPES:

        raise HTTPException(
            status_code=400,
            detail="File must be MP3, WAV, or M4A"
        )

    # =========================
    # Validate file size
    # =========================

    contents = await file.read()

    if len(contents) > 100 * 1024 * 1024:

        raise HTTPException(
            status_code=400,
            detail="File too large. Max 100MB"
        )

    # =========================
    # Create safe filename
    # =========================

    safe_filename = (
        file.filename
        .replace(" ", "_")
        .replace("/", "_")
    )

    file_id = str(uuid.uuid4())

    file_path = (
        f"{UPLOAD_DIR}/"
        f"{file_id}_{safe_filename}"
    )

    # =========================
    # Save temporary audio file
    # =========================

    try:

        with open(file_path, "wb") as f:
            f.write(contents)

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"File save failed: {str(e)}"
        )

    # =========================
    # Transcribe using Whisper
    # =========================

    try:

        with open(file_path, "rb") as audio_file:

            transcription = (
                client.audio.transcriptions.create(
                    model="whisper-large-v3",
                    file=audio_file,
                    language="en",
                    response_format="text"
                )
            )

    except Exception as e:

        if os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}"
        )

    # =========================
    # Cleanup temporary file
    # =========================

    if os.path.exists(file_path):
        os.remove(file_path)

    # =========================
    # Validate transcription
    # =========================

    if not transcription or not str(transcription).strip():

        raise HTTPException(
            status_code=500,
            detail="Empty transcription received"
        )

    # =========================
    # Save transcript to DB
    # =========================

    try:

        transcript_record = Transcript(
            id=uuid.uuid4(),
            session_id=session_id,
            raw_text=str(transcription)
        )

        db.add(transcript_record)

        db.commit()

        db.refresh(transcript_record)

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Database save failed: {str(e)}"
        )

    # =========================
    # Return response
    # =========================

    return {
        "transcript": str(transcription),
        "transcript_id": str(transcript_record.id),
        "session_id": session_id
    }