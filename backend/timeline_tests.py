import sys
import unittest
from pathlib import Path
from datetime import date

# Add the backend directory to sys.path
_BACKEND_DIR = Path(__file__).resolve().parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from clinical_timeline import detect_trend, build_timeline, get_report_sorting_date

class MockReport:
    def __init__(self, id, report_date, ocr_text, ocr_status="ready", created_at=None):
        self.id = id
        self.report_date = report_date
        self.ocr_text = ocr_text
        self.ocr_status = ocr_status
        self.created_at = created_at or date.today()

class TestClinicalTimeline(unittest.TestCase):

    def test_trend_detection_insufficient_data(self):
        """
        Verify trend detection for empty or single element lists.
        """
        self.assertEqual(detect_trend("hemoglobin", []), "INSUFFICIENT_DATA")
        self.assertEqual(detect_trend("hemoglobin", [14.5]), "INSUFFICIENT_DATA")

    def test_trend_detection_improving_toward_normal(self):
        """
        Verify that values moving closer to normal range map to IMPROVING.
        Normal range for Hemoglobin: 12.0 - 17.0
        """
        # Low values moving up toward normal
        self.assertEqual(detect_trend("hemoglobin", [9.5, 11.0]), "IMPROVING")
        # High values moving down toward normal
        self.assertEqual(detect_trend("hemoglobin", [19.0, 17.5]), "IMPROVING")
        # Moving from outside to fully inside
        self.assertEqual(detect_trend("hemoglobin", [10.5, 14.5]), "IMPROVING")

    def test_trend_detection_declining_away_from_normal(self):
        """
        Verify that values moving further from normal range map to DECLINING.
        Normal range for Hemoglobin: 12.0 - 17.0
        """
        # Low values dropping further below normal
        self.assertEqual(detect_trend("hemoglobin", [11.0, 9.5]), "DECLINING")
        # High values rising further above normal
        self.assertEqual(detect_trend("hemoglobin", [17.5, 19.0]), "DECLINING")
        # Moving from inside to outside
        self.assertEqual(detect_trend("hemoglobin", [14.5, 19.0]), "DECLINING")

    def test_trend_detection_stable(self):
        """
        Verify that stable values (or values staying within normal range) map to STABLE.
        Normal range for Hemoglobin: 12.0 - 17.0
        """
        # Constantly at same value
        self.assertEqual(detect_trend("hemoglobin", [14.5, 14.5]), "STABLE")
        # Staying inside the normal range (both distances are 0.0)
        self.assertEqual(detect_trend("hemoglobin", [13.0, 16.0]), "STABLE")
        # Floating point epsilon safety (diff <= 0.0001)
        self.assertEqual(detect_trend("hemoglobin", [18.0, 18.00001]), "STABLE")

    def test_single_report_timeline(self):
        """
        Verify single report timeline outputs.
        """
        ocr_content = "Hemoglobin Colorimetric 14.5 g/dL WBC Count 10570 RBC Count 4.79"
        reports = [
            MockReport(id="rep-1", report_date=date(2023, 2, 20), ocr_text=ocr_content)
        ]
        
        timeline = build_timeline(reports)
        
        # Check Hemoglobin
        self.assertEqual(timeline["hemoglobin"]["latest_value"], "14.5 g/dL")
        self.assertEqual(timeline["hemoglobin"]["latest_date"], "2023-02-20")
        self.assertEqual(timeline["hemoglobin"]["trend"], "INSUFFICIENT_DATA")
        self.assertEqual(timeline["hemoglobin"]["report_count"], 1)
        self.assertEqual(len(timeline["hemoglobin"]["history"]), 1)
        
        # Check WBC
        self.assertEqual(timeline["wbc"]["latest_value"], "10570")
        self.assertEqual(timeline["wbc"]["trend"], "INSUFFICIENT_DATA")
        self.assertEqual(timeline["wbc"]["report_count"], 1)
        
        # Check Platelets (not in report)
        self.assertIsNone(timeline["platelets"]["latest_value"])
        self.assertEqual(timeline["platelets"]["trend"], "INSUFFICIENT_DATA")
        self.assertEqual(timeline["platelets"]["report_count"], 0)
        self.assertEqual(len(timeline["platelets"]["history"]), 0)

    def test_multi_report_timeline_and_trends(self):
        """
        Verify multi-report chronological sorting and reference-range trends.
        """
        reports = [
            # Newer report - Hemoglobin goes to 19.5 (hyper) -> further from normal -> DECLINING
            # WBC goes to 12500 (hyper) -> further from normal -> DECLINING
            MockReport(
                id="rep-2", 
                report_date=date(2023, 3, 20), 
                ocr_text="Hemoglobin Colorimetric 19.5 g/dL WBC Count 12500"
            ),
            # Older report - Hemoglobin starts at 17.5 (slightly high)
            # WBC starts at 11500 (slightly high)
            MockReport(
                id="rep-1", 
                report_date=date(2023, 2, 20), 
                ocr_text="Hemoglobin Colorimetric 17.5 g/dL WBC Count 11500"
            )
        ]
        
        timeline = build_timeline(reports)
        
        # Hemoglobin went from 17.5 to 19.5 -> further from normal -> DECLINING
        self.assertEqual(timeline["hemoglobin"]["latest_value"], "19.5 g/dL")
        self.assertEqual(timeline["hemoglobin"]["latest_date"], "2023-03-20")
        self.assertEqual(timeline["hemoglobin"]["trend"], "DECLINING")
        self.assertEqual(timeline["hemoglobin"]["report_count"], 2)
        self.assertEqual(len(timeline["hemoglobin"]["history"]), 2)
        
        # WBC went from 11500 to 12500 -> further from normal -> DECLINING
        self.assertEqual(timeline["wbc"]["latest_value"], "12500")
        self.assertEqual(timeline["wbc"]["latest_date"], "2023-03-20")
        self.assertEqual(timeline["wbc"]["trend"], "DECLINING")
        self.assertEqual(timeline["wbc"]["report_count"], 2)

    def test_missing_values_graceful_handling(self):
        """
        Verify that missing tests across reports are handled gracefully.
        """
        reports = [
            MockReport(
                id="rep-1", 
                report_date=date(2023, 2, 20), 
                ocr_text="Hemoglobin Colorimetric 14.5 g/dL"
            ),
            MockReport(
                id="rep-2", 
                report_date=date(2023, 3, 20), 
                ocr_text="WBC Count 10500"
            )
        ]
        
        timeline = build_timeline(reports)
        
        # Hemoglobin only in rep-1
        self.assertEqual(len(timeline["hemoglobin"]["history"]), 1)
        self.assertEqual(timeline["hemoglobin"]["latest_value"], "14.5 g/dL")
        self.assertEqual(timeline["hemoglobin"]["trend"], "INSUFFICIENT_DATA")
        self.assertEqual(timeline["hemoglobin"]["report_count"], 1)
        
        # WBC only in rep-2
        self.assertEqual(len(timeline["wbc"]["history"]), 1)
        self.assertEqual(timeline["wbc"]["latest_value"], "10500")
        self.assertEqual(timeline["wbc"]["trend"], "INSUFFICIENT_DATA")
        self.assertEqual(timeline["wbc"]["report_count"], 1)

if __name__ == "__main__":
    unittest.main()
