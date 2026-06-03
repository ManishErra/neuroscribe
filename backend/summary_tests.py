import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import date

# Add the backend directory to sys.path
_BACKEND_DIR = Path(__file__).resolve().parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from clinical_summary import generate_clinical_summary_data
from clinical_timeline import build_timeline
from clinical_comparison import generate_comparison
from patient_insights import router
from fastapi.testclient import TestClient
from fastapi import FastAPI
from database import get_db

# Create a small test FastAPI app to test the router in isolation
test_app = FastAPI()
test_app.include_router(router)

class MockReportModel:
    def __init__(self, id, patient_id, ocr_text, report_date, ocr_status="ready", created_at=None):
        self.id = id
        self.patient_id = patient_id
        self.ocr_text = ocr_text
        self.report_date = report_date
        self.ocr_status = ocr_status
        self.created_at = created_at or date.today()

class MockPatientModel:
    def __init__(self, id, name, age=45, gender="Male"):
        self.id = id
        self.name = name
        self.age = age
        self.gender = gender

class TestClinicalSummaryAndInsights(unittest.TestCase):

    def test_generate_clinical_summary_normal_cbc(self):
        """
        Verify that a completely normal CBC report generates STABLE status,
        Stable CBC flag, and routine wellness recommendations.
        """
        ocr_text = "Hemoglobin 14.5 g/dL WBC 7000 /cmm Platelets 250000 /cmm Glucose 90 mg/dL RBC 4.8 million/cmm"
        
        # Setup empty timeline/comparison for single report normal CBC
        reports = [
            MockReportModel("rep-1", "pat-1", ocr_text, date(2023, 1, 1))
        ]
        timeline = build_timeline(reports)
        comparison = generate_comparison(timeline)
        
        summary_res = generate_clinical_summary_data(
            patient_id="pat-1",
            latest_report_text=ocr_text,
            latest_report_date="2023-01-01",
            timeline_data=timeline,
            comparison_data=comparison
        )
        
        self.assertEqual(summary_res["patient_id"], "pat-1")
        self.assertIn("completely within normal reference ranges", summary_res["summary"])
        self.assertEqual(len(summary_res["abnormalities"]), 0)
        self.assertIn("Stable CBC", summary_res["clinical_flags"])
        self.assertTrue(any("All laboratory values are within reference ranges" in rec for rec in summary_res["recommendations"]))
        
        # Check all 5 findings present and classified as Normal
        self.assertEqual(len(summary_res["findings"]), 5)
        self.assertTrue(any("Hemoglobin: 14.5 g/dL (Normal)" in f for f in summary_res["findings"]))
        self.assertTrue(any("Glucose: 90 mg/dL (Normal)" in f for f in summary_res["findings"]))

    def test_generate_clinical_summary_low_hemoglobin_worsening(self):
        """
        Verify that low and declining hemoglobin triggers 'Low Hemoglobin - Worsening' flag
        and correct trend-aware recommendations.
        """
        ocr_1 = "Hemoglobin 11.5 g/dL"
        ocr_2 = "Hemoglobin 9.5 g/dL"  # Declining
        
        reports = [
            MockReportModel("rep-1", "pat-1", ocr_1, date(2023, 1, 1)),
            MockReportModel("rep-2", "pat-1", ocr_2, date(2023, 2, 1))
        ]
        timeline = build_timeline(reports)
        comparison = generate_comparison(timeline)
        
        summary_res = generate_clinical_summary_data(
            patient_id="pat-1",
            latest_report_text=ocr_2,
            latest_report_date="2023-02-01",
            timeline_data=timeline,
            comparison_data=comparison
        )
        
        self.assertIn("Low Hemoglobin - Worsening", summary_res["clinical_flags"])
        self.assertEqual(len(summary_res["abnormalities"]), 1)
        self.assertIn("Low hemoglobin of 9.5 g/dL", summary_res["abnormalities"][0])
        # Verify recommendation has trend-aware warning
        self.assertTrue(any("Hemoglobin is low and declining" in rec for rec in summary_res["recommendations"]))
        self.assertTrue(any("hematology consultation" in rec for rec in summary_res["recommendations"]))

    def test_generate_clinical_summary_low_hemoglobin_improving(self):
        """
        Verify that low but improving hemoglobin triggers 'Low Hemoglobin - Improving' flag.
        """
        ocr_1 = "Hemoglobin 9.5 g/dL"
        ocr_2 = "Hemoglobin 11.5 g/dL"  # Improving
        
        reports = [
            MockReportModel("rep-1", "pat-1", ocr_1, date(2023, 1, 1)),
            MockReportModel("rep-2", "pat-1", ocr_2, date(2023, 2, 1))
        ]
        timeline = build_timeline(reports)
        comparison = generate_comparison(timeline)
        
        summary_res = generate_clinical_summary_data(
            patient_id="pat-1",
            latest_report_text=ocr_2,
            latest_report_date="2023-02-01",
            timeline_data=timeline,
            comparison_data=comparison
        )
        
        self.assertIn("Low Hemoglobin - Improving", summary_res["clinical_flags"])
        self.assertTrue(any("Evaluate for nutritional deficiencies" in rec for rec in summary_res["recommendations"]))

    def test_generate_clinical_summary_high_wbc_worsening(self):
        """
        Verify that high and worsening WBC count triggers appropriate warning status
        and recommendation for localized/systemic infection screening.
        """
        ocr_1 = "WBC 11500"
        ocr_2 = "WBC 13500"  # Declining/Worsening (further away from normal)
        
        reports = [
            MockReportModel("rep-1", "pat-1", ocr_1, date(2023, 1, 1)),
            MockReportModel("rep-2", "pat-1", ocr_2, date(2023, 2, 1))
        ]
        timeline = build_timeline(reports)
        comparison = generate_comparison(timeline)
        
        summary_res = generate_clinical_summary_data(
            patient_id="pat-1",
            latest_report_text=ocr_2,
            latest_report_date="2023-02-01",
            timeline_data=timeline,
            comparison_data=comparison
        )
        
        self.assertIn("Elevated WBC - Worsening", summary_res["clinical_flags"])
        self.assertTrue(any("WBC count is elevated and worsening" in rec for rec in summary_res["recommendations"]))
        self.assertTrue(any("active localized/systemic infection" in rec for rec in summary_res["recommendations"]))

    def test_generate_clinical_summary_multiple_abnormalities(self):
        """
        Verify that multiple concurrent abnormalities produce multiple flags
        and multiple mapped recommendations.
        """
        ocr_text = "Hemoglobin 9.5 g/dL Glucose 140 mg/dL WBC 5000 Platelets 300000"
        
        reports = [
            MockReportModel("rep-1", "pat-1", ocr_text, date(2023, 1, 1))
        ]
        timeline = build_timeline(reports)
        comparison = generate_comparison(timeline)
        
        summary_res = generate_clinical_summary_data(
            patient_id="pat-1",
            latest_report_text=ocr_text,
            latest_report_date="2023-01-01",
            timeline_data=timeline,
            comparison_data=comparison
        )
        
        self.assertIn("Low Hemoglobin", summary_res["clinical_flags"])
        self.assertIn("Elevated Glucose", summary_res["clinical_flags"])
        self.assertEqual(len(summary_res["abnormalities"]), 2)
        self.assertTrue(any("Low hemoglobin" in ab for ab in summary_res["abnormalities"]))
        self.assertTrue(any("Elevated glucose" in ab for ab in summary_res["abnormalities"]))
        self.assertEqual(len(summary_res["recommendations"]), 2)

    def test_generate_clinical_summary_missing_data(self):
        """
        Verify that missing tests are handled gracefully and do not crash the engine.
        """
        # Report only has glucose
        ocr_text = "Glucose 95 mg/dL"
        
        reports = [
            MockReportModel("rep-1", "pat-1", ocr_text, date(2023, 1, 1))
        ]
        timeline = build_timeline(reports)
        comparison = generate_comparison(timeline)
        
        summary_res = generate_clinical_summary_data(
            patient_id="pat-1",
            latest_report_text=ocr_text,
            latest_report_date="2023-01-01",
            timeline_data=timeline,
            comparison_data=comparison
        )
        
        self.assertEqual(len(summary_res["findings"]), 1)
        self.assertEqual(summary_res["findings"][0], "Glucose: 95 mg/dL (Normal)")
        self.assertEqual(len(summary_res["abnormalities"]), 0)
        self.assertIn("Stable CBC", summary_res["clinical_flags"])

    def test_patient_insights_api_endpoints_mocked(self):
        """
        Verify endpoint routing, validation, and JSON key compliance using mocked DB sessions.
        """
        client = TestClient(test_app)
        
        # Create mock entities
        mock_patient = MockPatientModel("pat-123", "John Doe")
        mock_reports = [
            MockReportModel("rep-1", "pat-123", "Hemoglobin 14.5 g/dL Glucose 95 mg/dL", date(2023, 1, 1), ocr_status="ready"),
            MockReportModel("rep-2", "pat-123", "Hemoglobin 9.5 g/dL Glucose 140 mg/dL", date(2023, 2, 1), ocr_status="ready")
        ]
        
        # Set up a Mock DB session
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_patient
        mock_db.query.return_value.filter.return_value.all.return_value = mock_reports
        
        # Override the get_db dependency
        def override_get_db():
            yield mock_db
            
        test_app.dependency_overrides[get_db] = override_get_db
        
        try:
            # 1. Test GET /patient-insights/{patient_id}
            resp_insights = client.get("/patient-insights/pat-123")
            self.assertEqual(resp_insights.status_code, 200)
            
            data_ins = resp_insights.json()
            self.assertEqual(data_ins["patient_id"], "pat-123")
            self.assertIn("summary", data_ins)
            self.assertIn("findings", data_ins)
            self.assertIn("abnormalities", data_ins)
            self.assertIn("recommendations", data_ins)
            self.assertIn("clinical_flags", data_ins)
            
            # Since latest report has low hemoglobin (9.5) and high glucose (140), verify details
            self.assertIn("Low Hemoglobin - Worsening", data_ins["clinical_flags"])
            self.assertIn("Elevated Glucose - Worsening", data_ins["clinical_flags"])
            
            # 2. Test GET /patient-overview/{patient_id}
            resp_overview = client.get("/patient-overview/pat-123")
            self.assertEqual(resp_overview.status_code, 200)
            
            data_over = resp_overview.json()
            self.assertEqual(data_over["patient_id"], "pat-123")
            self.assertEqual(data_over["status"], "CRITICAL")  # 2 abnormalities
            self.assertIn("Low Hemoglobin - Worsening", data_over["clinical_flags"])
            self.assertIn("Elevated Glucose - Worsening", data_over["clinical_flags"])
            
            # Verify latest labs mapping
            self.assertEqual(data_over["latest_labs"]["hemoglobin"], "9.5 g/dL")
            self.assertEqual(data_over["latest_labs"]["glucose"], "140 mg/dL")
            
            # Verify last activity
            self.assertEqual(data_over["last_activity"]["type"], "laboratory_report")
            self.assertEqual(data_over["last_activity"]["date"], "2023-02-01")
            self.assertEqual(data_over["last_activity"]["id"], "rep-2")
            
        finally:
            test_app.dependency_overrides.clear()

if __name__ == "__main__":
    unittest.main()
