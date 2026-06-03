from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from database import get_db
from models import Patient, Report
from clinical_timeline import build_timeline
from clinical_comparison import generate_comparison
from auth_utils import get_current_user

router = APIRouter(prefix="/compare", tags=["Comparison"], dependencies=[Depends(get_current_user)])

@router.get("/{patient_id}")
def get_patient_comparison(patient_id: str, db: DBSession = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Get clinical laboratory comparison and change detection for a patient.
    """
    # 1. Verify patient exists and is owned by user
    patient = db.query(Patient).filter(Patient.id == patient_id, Patient.owner_id == current_user.id).first()
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
