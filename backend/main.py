from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.audio import router as audio_router
from routers.notes import router as notes_router
app = FastAPI()

app.include_router(audio_router)
app.include_router(notes_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(audio_router)

@app.get("/")
def root():
    return {"message": "NeuroScribe backend running"}

@app.get("/db-test")
def db_test():
    with engine.connect() as conn:
        return {"db": "connected"}