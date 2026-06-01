from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from database import get_db
from models import Patient, Report
from clinical_timeline import build_timeline
from clinical_comparison import generate_comparison

router = APIRouter(prefix="/compare", tags=["Comparison"])

@router.get("/{patient_id}")
def get_patient_comparison(patient_id: str, db: DBSession = Depends(get_db)):
    """
    Get clinical laboratory comparison and change detection for a patient.
    """
    # 1. Verify patient exists
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found"
        )
        
    # 2. Get all reports for the patient
    reports = db.query(Report).filter(Report.patient_id == patient_id).all()
    
    # 3. Build clinical timeline
    timeline_data = build_timeline(reports)
    
    # 4. Generate comparison metrics
    comparison_data = generate_comparison(timeline_data)
    
    return {
        "patient_id": patient_id,
        "patient_name": patient.name,
        "comparison": comparison_data
    }
