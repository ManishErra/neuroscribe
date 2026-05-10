from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi import Depends
from groq import Groq
from database import get_db
from models import Transcript
from sqlalchemy.orm import Session as DBSession

import os, shutil, uuid
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_TYPES = [
    "audio/mpeg",
    "audio/wav",
    "audio/mp4",
    "audio/x-m4a",
    "audio/webm"
]

@router.post("/upload-audio")
async def upload_audio(
    file: UploadFile = File(...),
    patient_id: str = None,
    db: DBSession = Depends(get_db)
):

    # 1. Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="File must be MP3, WAV, or M4A"
        )

    # 2. Validate file size (100MB max)
    contents = await file.read()

    if len(contents) > 100 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File too large. Max 100MB"
        )

    # 3. Save file
    file_id = str(uuid.uuid4())

    file_path = f"{UPLOAD_DIR}/{file_id}_{file.filename}"

    with open(file_path, "wb") as f:
        f.write(contents)

    # 4. Send to Groq Whisper
    try:
        with open(file_path, "rb") as audio_file:

            transcription = client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=audio_file,
                language="en",
                response_format="text"
            )

    except Exception as e:

        if os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}"
        )
    # 5. Delete audio after transcription
    if os.path.exists(file_path):
        os.remove(file_path)

    # Save transcript to DB
    transcript_record = Transcript(
        id=uuid.uuid4(),
        session_id=None,
        raw_text=transcription
    )

    db.add(transcript_record)
    db.commit()
    db.refresh(transcript_record)

    return {
        "transcript": transcription,
        "transcript_id": str(transcript_record.id)
    }