from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine
from routers.audio import router as audio_router
from routers.notes import router as notes_router
from routers.patients import router as patients_router
from routers.sessions import router as sessions_router

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(audio_router)
app.include_router(notes_router)
app.include_router(patients_router)
app.include_router(sessions_router)

@app.get("/")
def root():
    return {"message": "NeuroScribe backend running"}

@app.get("/db-test")
def db_test():
    with engine.connect() as conn:
        return {"db": "connected"}