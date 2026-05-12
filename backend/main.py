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
    router as search_router
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

app.include_router(search_router)


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