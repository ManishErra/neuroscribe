from fastapi import (
    APIRouter,
    HTTPException,
    Depends
)

from pydantic import BaseModel

from sqlalchemy.orm import (
    Session as DBSession
)

from sqlalchemy import text

from database import get_db

from models import (
    Note,
    Embedding,
    Session as SessionModel,
    Patient
)

from embeddings import (
    generate_embedding,
    chunk_text
)

from auth_utils import get_current_user
import uuid
import json

router = APIRouter(
    prefix="/embed",
    dependencies=[Depends(get_current_user)]
)

# =========================
# REQUEST MODEL
# =========================

class EmbedRequest(BaseModel):

    note_id: str

# =========================
# EMBED NOTE
# =========================

@router.post("/note")
def embed_note(
    req: EmbedRequest,
    db: DBSession = Depends(get_db),
    current_user = Depends(get_current_user)
):

    # =========================
    # FETCH NOTE
    # =========================

    note = db.query(Note).filter(
        Note.id == req.note_id
    ).first()

    if not note:

        raise HTTPException(
            404,
            "Note not found"
        )

    # Verify patient ownership via session
    session = db.query(SessionModel).filter(SessionModel.id == note.session_id).first()
    if not session:
        raise HTTPException(404, "Note not found")
        
    patient = db.query(Patient).filter(
        Patient.id == session.patient_id,
        Patient.owner_id == current_user.id
    ).first()
    if not patient:
        raise HTTPException(404, "Note not found")

    if not note.is_finalized:

        raise HTTPException(
            400,
            "Only finalized notes can be embedded"
        )

    # =========================
    # USE FINALIZED VERSION
    # =========================

    note_text = note.doctor_edited

    if not note_text:

        raise HTTPException(
            400,
            "No finalized note text found"
        )

    # =========================
    # CONVERT JSON TO TEXT
    # =========================

    try:

        note_dict = json.loads(
            note_text
        )

        plain_text = " ".join([

            f"{k}: {v}"

            for k, v in note_dict.items()

            if v and str(v).strip()
        ])

    except Exception:

        plain_text = note_text

    # =========================
    # CHUNK NOTE
    # =========================

    chunks = chunk_text(
        plain_text,
        chunk_size=200,
        overlap=20
    )

    stored = 0

    # =========================
    # EMBED + STORE
    # =========================

    for chunk in chunks:

        vec = generate_embedding(
            chunk
        )

        db.execute(text("""

            INSERT INTO embeddings
            (
                id,
                source_id,
                source_type,
                chunk_text,
                embedding,
                owner_id
            )

            VALUES
            (
                :id,
                :source_id,
                :source_type,
                :chunk_text,
                :embedding,
                :owner_id
            )

        """), {

            "id": str(uuid.uuid4()),

            "source_id": str(note.id),

            "source_type": "note",

            "chunk_text": chunk,

            "embedding": str(vec),

            "owner_id": str(current_user.id)
        })

        stored += 1

    # =========================
    # COMMIT
    # =========================

    db.commit()

    return {

        "chunks_stored": stored,

        "note_id": req.note_id
    }