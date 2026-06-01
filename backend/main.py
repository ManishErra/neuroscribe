import sys
from pathlib import Path

# Add backend directory to sys.path to guarantee that unmodified local absolute imports 
# in the repository (e.g. from audio.py, notes.py) resolve cleanly.
_BACKEND_DIR = Path(__file__).resolve().parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from fastapi import FastAPI

from fastapi.middleware.cors import (
    CORSMiddleware
)

from database import engine


# =========================================
# ROUTERS
# =========================================

from routers.audio import (
    router as audio_router
)

from routers.notes import (
    router as notes_router
)

from routers.patients import (
    router as patients_router
)

from routers.sessions import (
    router as sessions_router
)

from routers.embed import (
    router as embed_router
)

from routers.search import (
    router as ask_router
)

from routers.reports import (
    router as reports_router
)

from routers.timeline import (
    router as timeline_router
)

from routers.comparison import (
    router as comparison_router
)

from patient_insights import (
    router as patient_insights_router
)


# =========================================
# FASTAPI APP
# =========================================

app = FastAPI(

    title="NeuroScribe API",

    description=(
        "AI-powered psychiatric "
        "clinical documentation "
        "and semantic retrieval system."
    ),

    version="0.1.0"

)


# =========================================
# CORS
# =========================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=[
        "http://localhost:3000"
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]

)


# =========================================
# ROUTER REGISTRATION
# =========================================

app.include_router(audio_router)

app.include_router(notes_router)

app.include_router(patients_router)

app.include_router(sessions_router)

app.include_router(embed_router)

app.include_router(ask_router)

app.include_router(reports_router)

app.include_router(timeline_router)

app.include_router(comparison_router)

app.include_router(patient_insights_router)


# =========================================
# ROOT ENDPOINT
# =========================================

@app.get("/")
def root():

    return {

        "message": (
            "NeuroScribe backend running"
        )

    }


# =========================================
# DATABASE TEST
# =========================================

@app.get("/db-test")
def db_test():

    with engine.connect() as conn:

        return {

            "db": "connected"

        }