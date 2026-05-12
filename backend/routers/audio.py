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

from models import (
    Transcript,
    Session as SessionModel
)

import os
import uuid

from dotenv import load_dotenv


# =========================================
# LOAD ENVIRONMENT
# =========================================

load_dotenv()


# =========================================
# ROUTER
# =========================================

router = APIRouter()


# =========================================
# GROQ CLIENT
# =========================================

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


# =========================================
# CONFIG
# =========================================

UPLOAD_DIR = "uploads"

MAX_FILE_SIZE_MB = 100

MAX_FILE_SIZE_BYTES = (
    MAX_FILE_SIZE_MB * 1024 * 1024
)

ALLOWED_TYPES = [

    "audio/mpeg",

    "audio/wav",

    "audio/mp4",

    "audio/x-m4a",

    "audio/webm"
]

# =========================================
# TEST DATASET MODE
# Turn OFF later for production
# =========================================

TEST_MODE = False


# =========================================
# CREATE UPLOAD FOLDER
# =========================================

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)


# =========================================
# FAKE TEST TRANSCRIPTS
# =========================================

TEST_TRANSCRIPTS = [

    """
    Patient reports worsening anxiety over the last month.
    Difficulty sleeping 4 to 5 hours nightly.
    Feels overwhelmed with work pressure.
    No medications currently.
    Plan discussed: stress management and therapy referral.
    """,

    """
    Patient reports persistent low mood and fatigue.
    Sleep reduced to 3 to 4 hours nightly.
    Difficulty concentrating at work.
    Started sertraline 50mg daily.
    Patient reports social withdrawal.
    """,

    """
    Patient reports improved mood after starting medication.
    Sleeping 6 to 7 hours nightly.
    Less anxious during social situations.
    Continuing sertraline with no major side effects.
    Discussed exercise and maintaining routine.
    """
]


# =========================================
# HELPERS
# =========================================

def validate_audio_type(content_type: str):

    if content_type not in ALLOWED_TYPES:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported audio format. "
                "Use MP3, WAV, M4A, or WEBM."
            )
        )


def validate_audio_size(contents: bytes):

    if len(contents) > MAX_FILE_SIZE_BYTES:

        raise HTTPException(
            status_code=400,
            detail=(
                f"File too large. "
                f"Max {MAX_FILE_SIZE_MB}MB"
            )
        )


def create_safe_filename(filename: str):

    safe_name = (
        filename
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
    )

    return (
        f"{uuid.uuid4()}_{safe_name}"
    )


def cleanup_file(path: str):

    try:

        if os.path.exists(path):
            os.remove(path)

    except Exception:
        pass


# =========================================
# AUDIO UPLOAD ENDPOINT
# =========================================

@router.post("/upload-audio")
async def upload_audio(

    session_id: str = Form(...),

    file: UploadFile = File(...),

    db: DBSession = Depends(get_db)

):

    # =====================================
    # VALIDATE SESSION
    # =====================================

    existing_session = (
        db.query(SessionModel)
        .filter(
            SessionModel.id == session_id
        )
        .first()
    )

    if not existing_session:

        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    # =====================================
    # VALIDATE FILE TYPE
    # =====================================

    validate_audio_type(
        file.content_type
    )

    # =====================================
    # READ FILE
    # =====================================

    contents = await file.read()

    validate_audio_size(contents)

    # =====================================
    # SAVE TEMP FILE
    # =====================================

    filename = create_safe_filename(
        file.filename
    )

    file_path = (
        f"{UPLOAD_DIR}/{filename}"
    )

    try:

        with open(file_path, "wb") as f:
            f.write(contents)

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"File save failed: {str(e)}"
        )

    # =====================================
    # TRANSCRIPTION
    # =====================================

    try:

        # ---------------------------------
        # TEST MODE
        # ---------------------------------

        if TEST_MODE:

            existing_count = (
                db.query(Transcript)
                .filter(
                    Transcript.session_id == session_id
                )
                .count()
            )

            transcript_text = TEST_TRANSCRIPTS[
                existing_count % len(TEST_TRANSCRIPTS)
            ]

        # ---------------------------------
        # REAL WHISPER MODE
        # ---------------------------------

        else:

            with open(file_path, "rb") as audio_file:

                transcription = (
                    client.audio.transcriptions.create(

                        model="whisper-large-v3",

                        file=audio_file,

                        language="en",

                        response_format="text"
                    )
                )

            transcript_text = str(
                transcription
            )

    except Exception as e:

        cleanup_file(file_path)

        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}"
        )

    # =====================================
    # CLEANUP TEMP FILE
    # =====================================

    cleanup_file(file_path)

    # =====================================
    # VALIDATE TRANSCRIPT
    # =====================================

    if not transcript_text.strip():

        raise HTTPException(
            status_code=500,
            detail="Empty transcription received"
        )

    # =====================================
    # SAVE TO DATABASE
    # =====================================

    try:

        transcript_record = Transcript(

            id=uuid.uuid4(),

            session_id=session_id,

            raw_text=transcript_text.strip()
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

    # =====================================
    # SUCCESS RESPONSE
    # =====================================

    return {

        "success": True,

        "message":
            "Transcript saved successfully.",

        "test_mode":
            TEST_MODE,

        "transcript":
            transcript_text.strip(),

        "transcript_id":
            str(transcript_record.id),

        "session_id":
            session_id
    }