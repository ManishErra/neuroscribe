import json
import sys
from clinical_entities import extract_clinical_entities
from clinical_extractors import extract_hemoglobin
from clinical_flags import classify_lab_result
from llm_service import generate_answer

def run_all_tests():
    print("Starting NeuroScribe Clinical Extraction Test Suite...")
    print("-" * 50)

    try:
        # Test 1: Hemoglobin Extraction
        print("Testing Hemoglobin Extraction...", end=" ")
        text = "Hemoglobin = 14.5 g/dL"
        entities = extract_clinical_entities(text)
        assert entities.get("hemoglobin") == "14.5 g/dL", f"Expected '14.5 g/dL', got '{entities.get('hemoglobin')}'"
        val = extract_hemoglobin(text)
        assert val == "14.5 g/dL", f"Expected '14.5 g/dL', got '{val}'"

        # Regression Test: actual OCR chunk with just single space "Hemoglobin 14.5 g/dL"
        text_ocr = "Hemoglobin 14.5 g/dL"
        entities_ocr = extract_clinical_entities(text_ocr)
        assert entities_ocr.get("hemoglobin") == "14.5 g/dL", f"Expected '14.5 g/dL', got '{entities_ocr.get('hemoglobin')}'"
        val_ocr = extract_hemoglobin(text_ocr)
        assert val_ocr == "14.5 g/dL", f"Expected '14.5 g/dL', got '{val_ocr}'"

        # Regression Test: real methodology word "Hemoglobin Colorimetric 14.5 g/dL"
        text_real = "Hemoglobin Colorimetric 14.5 g/dL"
        entities_real = extract_clinical_entities(text_real)
        assert entities_real.get("hemoglobin") == "14.5 g/dL", f"Expected '14.5 g/dL', got '{entities_real.get('hemoglobin')}'"
        val_real = extract_hemoglobin(text_real)
        assert val_real == "14.5 g/dL", f"Expected '14.5 g/dL', got '{val_real}'"
        print("PASSED")

        # Test 2: HbA1c Prevention
        print("Testing HbA1c Prevention...", end=" ")
        text = "HbA1c = 6.0 %"
        entities = extract_clinical_entities(text)
        assert "hemoglobin" not in entities, f"Expected no hemoglobin match, got '{entities.get('hemoglobin')}'"
        val = extract_hemoglobin(text)
        assert val is None, f"Expected None, got '{val}'"

        # HbA2 prevention
        text2 = "Hb A2 = 2.5 %"
        entities2 = extract_clinical_entities(text2)
        assert "hemoglobin" not in entities2, f"Expected no hemoglobin match for Hb A2, got '{entities2.get('hemoglobin')}'"
        val2 = extract_hemoglobin(text2)
        assert val2 is None, f"Expected None for Hb A2, got '{val2}'"
        print("PASSED")

        # Test 3: WBC Extraction
        print("Testing WBC Extraction...", end=" ")
        text = "WBC Count ... 10570 /cmm"
        entities = extract_clinical_entities(text)
        assert entities.get("wbc") == "10570", f"Expected '10570', got '{entities.get('wbc')}'"
        print("PASSED")

        # Test 4: Platelets Extraction
        print("Testing Platelets Extraction...", end=" ")
        text = "Platelet Count ----- 150000 /cmm"
        entities = extract_clinical_entities(text)
        assert entities.get("platelets") == "150000", f"Expected '150000', got '{entities.get('platelets')}'"
        print("PASSED")

        # Test 5: RBC Extraction
        print("Testing RBC Extraction...", end=" ")
        text = "RBC Count | 4.79 million/cmm"
        entities = extract_clinical_entities(text)
        assert entities.get("rbc") == "4.79", f"Expected '4.79', got '{entities.get('rbc')}'"
        print("PASSED")

        # Test 6: OCR Noise Tolerance
        print("Testing OCR Noise Tolerance...", end=" ")
        # intermediate words, e.g. "WBC Count SF Cube cell analysis 10570"
        text = "WBC Count SF Cube cell analysis 10570"
        entities = extract_clinical_entities(text)
        assert entities.get("wbc") == "10570", f"Expected '10570' under noise, got '{entities.get('wbc')}'"

        # Messy spacing and extra characters for Platelets
        text_plt = "Platelets level (by manual method) :::::::   150000 per microliter"
        entities_plt = extract_clinical_entities(text_plt)
        assert entities_plt.get("platelets") == "150000", f"Expected '150000' under noise, got '{entities_plt.get('platelets')}'"

        # Messy spacing and extra characters for RBC
        text_rbc = "RBC (Red Blood Cell Count) -- -- -- -- -- 4.79 million/cu mm"
        entities_rbc = extract_clinical_entities(text_rbc)
        assert entities_rbc.get("rbc") == "4.79", f"Expected '4.79' under noise, got '{entities_rbc.get('rbc')}'"
        print("PASSED")

        # Test 7: End-to-End Answer Generation (Deterministic Steps)
        print("Testing End-to-End Answer Generation...", end=" ")
        context = """
        Patient Profile: Male 45 years
        ---------------------------------------------------------
        Test Description                     Result      Reference
        ---------------------------------------------------------
        Hemoglobin                           14.5 g/dL   12-17
        WBC Count SF Cube cell analysis      10570       4000-11000
        RBC Count |                          4.79        4.5-5.9
        Platelet Count -----                 150000      150000-450000
        HbA1c (Glycated Hemoglobin)          6.0 %       4.0-5.6
        ---------------------------------------------------------
        """

        # 1. Hemoglobin
        ans_hb = generate_answer(context, "What is the hemoglobin level?")
        data_hb = json.loads(ans_hb)
        assert data_hb["test"] == "hemoglobin"
        assert data_hb["value"] == "14.5 g/dL"
        assert data_hb["status"] == "NORMAL"

        # 2. WBC
        ans_wbc = generate_answer(context, "What is the WBC count?")
        data_wbc = json.loads(ans_wbc)
        assert data_wbc["test"] == "wbc"
        assert data_wbc["value"] == "10570"
        assert data_wbc["unit"] == "/cmm"
        assert data_wbc["status"] == "NORMAL"

        # 3. Platelets
        ans_plt = generate_answer(context, "What is the platelet count?")
        data_plt = json.loads(ans_plt)
        assert data_plt["test"] == "platelets"
        assert data_plt["value"] == "150000"
        assert data_plt["unit"] == "/cmm"
        assert data_plt["status"] == "NORMAL"

        # 4. RBC
        ans_rbc = generate_answer(context, "What is the RBC count?")
        data_rbc = json.loads(ans_rbc)
        assert data_rbc["test"] == "rbc"
        assert data_rbc["value"] == "4.79"
        assert data_rbc["unit"] == "million/cmm"
        assert data_rbc["status"] == "NORMAL"
        print("PASSED")

        print("-" * 50)
        print("ALL TESTS PASSED SUCCESSFULLY! Clean clinical extraction verified.")
        return 0

    except AssertionError as e:
        print("FAILED")
        print("\nAssertion Error encountered:")
        print(e)
        return 1
    except Exception as e:
        print("ERROR")
        print("\nUnexpected error occurred:")
        print(e)
        return 2

if __name__ == "__main__":
    sys.exit(run_all_tests())
