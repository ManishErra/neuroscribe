import sys
import os
from pathlib import Path

# Add backend directory to sys.path to guarantee that unmodified local absolute imports 
# in the repository (e.g. from audio.py, notes.py) resolve cleanly.
_BACKEND_DIR = Path(__file__).resolve().parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

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

from routers.auth import (
    router as auth_router
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
# SECURITY HEADERS
# =========================================

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    if os.getenv("APP_ENV", "development").lower() == "production":
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data:; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self' 'unsafe-inline';"
        )
    return response


# =========================================
# CORS
# =========================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173"
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]

)


# =========================================
# STATIC FILE SERVING
# =========================================

uploads_dir = Path(__file__).resolve().parent / "uploads"
uploads_dir.mkdir(parents=True, exist_ok=True)


# =========================================
# STARTUP VALIDATION
# =========================================

@app.on_event("startup")
def startup_validation():
    from startup_validation import validate_startup_environment
    validate_startup_environment()


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

app.include_router(auth_router)



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

