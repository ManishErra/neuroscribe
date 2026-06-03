import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# Mock sentence-transformers to avoid slow network/Hugging Face loading in sandbox
sys.modules['sentence_transformers'] = MagicMock()

# Add backend directory to sys.path
_BACKEND_DIR = Path(__file__).resolve().parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from clinical_comparison import calculate_change_metrics
from fastapi.testclient import TestClient
from main import app

class TestClinicalComparison(unittest.TestCase):

    def test_insufficient_history(self):
        """
        Verify INSUFFICIENT_DATA is returned for history lengths < 2.
        """
        # Empty history
        res_empty = calculate_change_metrics("hemoglobin", [])
        self.assertEqual(res_empty["change_classification"], "INSUFFICIENT_DATA")
        self.assertIsNone(res_empty["absolute_change"])
        
        # Single element history
        single_hist = [{"value": "14.5 g/dL", "numeric_value": 14.5}]
        res_single = calculate_change_metrics("hemoglobin", single_hist)
        self.assertEqual(res_single["change_classification"], "INSUFFICIENT_DATA")
        self.assertEqual(res_single["current_value"], "14.5 g/dL")

    def test_clinically_insignificant_changes(self):
        """
        Verify that changes below the significance thresholds map to STABLE.
        Hb threshold: 0.5, PLT threshold: 10000, WBC threshold: 500
        """
        # Hemoglobin change of 0.3 (below 0.5 threshold)
        hist_hb = [
            {"value": "10.0 g/dL", "numeric_value": 10.0},
            {"value": "10.3 g/dL", "numeric_value": 10.3}
        ]
        res_hb = calculate_change_metrics("hemoglobin", hist_hb)
        self.assertEqual(res_hb["change_classification"], "STABLE")
        self.assertEqual(res_hb["absolute_change"], 0.3)
        self.assertEqual(res_hb["percentage_change"], 3.0)

        # WBC change of 400 (below 500 threshold)
        hist_wbc = [
            {"value": "12000", "numeric_value": 12000.0},
            {"value": "12400", "numeric_value": 12400.0}
        ]
        res_wbc = calculate_change_metrics("wbc", hist_wbc)
        self.assertEqual(res_wbc["change_classification"], "STABLE")
        self.assertEqual(res_wbc["absolute_change"], 400.0)

    def test_significant_improvements(self):
        """
        Verify that significant changes moving toward the reference range map to IMPROVED.
        Hb threshold: 0.5 (low: 12.0, high: 17.0)
        WBC threshold: 500 (low: 4000, high: 11000)
        """
        # Low Hemoglobin rising significantly toward normal limits (from 9.0 to 11.5)
        hist_hb = [
            {"value": "9.0 g/dL", "numeric_value": 9.0},
            {"value": "11.5 g/dL", "numeric_value": 11.5}
        ]
        res_hb = calculate_change_metrics("hemoglobin", hist_hb)
        self.assertEqual(res_hb["change_classification"], "IMPROVED")
        self.assertEqual(res_hb["absolute_change"], 2.5)

        # High WBC dropping significantly toward normal limits (from 13000 to 10500)
        hist_wbc = [
            {"value": "13000", "numeric_value": 13000.0},
            {"value": "10500", "numeric_value": 10500.0}
        ]
        res_wbc = calculate_change_metrics("wbc", hist_wbc)
        self.assertEqual(res_wbc["change_classification"], "IMPROVED")
        self.assertEqual(res_wbc["absolute_change"], -2500.0)

    def test_significant_worsening(self):
        """
        Verify that significant changes moving away from reference ranges map to WORSENED.
        PLT threshold: 10000 (low: 150000, high: 450000)
        """
        # Platelets dropping significantly further below normal (from 140000 to 110000)
        hist_plt = [
            {"value": "140000", "numeric_value": 140000.0},
            {"value": "110000", "numeric_value": 110000.0}
        ]
        res_plt = calculate_change_metrics("platelets", hist_plt)
        self.assertEqual(res_plt["change_classification"], "WORSENED")
        self.assertEqual(res_plt["absolute_change"], -30000.0)

    def test_compare_api_routing(self):
        """
        Verify that the GET /compare/{patient_id} endpoint routes successfully.
        """
        client = TestClient(app)
        # Query the real patient Radhika Erra in database
        patient_id = "51773efc-479b-469d-931d-cd483786c20e"
        
        response = client.get(f"/compare/{patient_id}")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["patient_id"], patient_id)
        self.assertEqual(data["patient_name"], "Radhika Erra")
        self.assertIn("comparison", data)
        
        # Platelets and RBC should have at least 23 records in Radhika's history,
        # and stay relatively stable (same values in the synthetic reports).
        # We assert that the classifications are correctly fetched.
        self.assertIn("platelets", data["comparison"])
        self.assertEqual(data["comparison"]["platelets"]["change_classification"], "STABLE")

if __name__ == "__main__":
    unittest.main()
