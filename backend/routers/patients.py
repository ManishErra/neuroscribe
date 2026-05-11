from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession

from database import get_db
from models import Patient

import uuid

router = APIRouter(prefix="/patients")


class PatientCreate(BaseModel):
    name: str
    age: int
    gender: str


# GET all patients
@router.get("/")
def get_all_patients(db: DBSession = Depends(get_db)):
    patients = db.query(Patient).order_by(Patient.created_at.desc()).all()

    return [
        {
            "id": str(p.id),
            "name": p.name,
            "age": p.age,
            "gender": p.gender,
            "created_at": str(p.created_at)
        }
        for p in patients
    ]


# GET single patient
@router.get("/{patient_id}")
def get_patient(patient_id: str, db: DBSession = Depends(get_db)):
    p = db.query(Patient).filter(Patient.id == patient_id).first()

    if not p:
        raise HTTPException(404, "Patient not found")

    return {
        "id": str(p.id),
        "name": p.name,
        "age": p.age,
        "gender": p.gender
    }


# POST create patient
@router.post("/")
def create_patient(data: PatientCreate, db: DBSession = Depends(get_db)):

    if not data.name.strip():
        raise HTTPException(400, "Name cannot be empty")

    if data.age < 1 or data.age > 120:
        raise HTTPException(400, "Age must be between 1 and 120")

    patient = Patient(
        id=uuid.uuid4(),
        name=data.name.strip(),
        age=data.age,
        gender=data.gender
    )

    db.add(patient)
    db.commit()
    db.refresh(patient)

    return {
        "id": str(patient.id),
        "name": patient.name
    }


# DELETE patient
@router.delete("/{patient_id}")
def delete_patient(patient_id: str, db: DBSession = Depends(get_db)):

    p = db.query(Patient).filter(Patient.id == patient_id).first()

    if not p:
        raise HTTPException(404, "Patient not found")

    db.delete(p)
    db.commit()

    return {"deleted": patient_id}