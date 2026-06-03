import json
import pytest
from clinical_entities import extract_clinical_entities
from clinical_extractors import extract_hemoglobin
from clinical_flags import classify_lab_result
from llm_service import generate_answer, try_structured_entity_answer


def test_hemoglobin_extraction():
    # Valid hemoglobin matching
    text = "Hemoglobin = 14.5 g/dL"
    entities = extract_clinical_entities(text)
    assert entities.get("hemoglobin") == "14.5 g/dL"

    val = extract_hemoglobin(text)
    assert val == "14.5 g/dL"

    # Regression: actual OCR chunk with just single space "Hemoglobin 14.5 g/dL"
    text_ocr = "Hemoglobin 14.5 g/dL"
    entities_ocr = extract_clinical_entities(text_ocr)
    assert entities_ocr.get("hemoglobin") == "14.5 g/dL"
    val_ocr = extract_hemoglobin(text_ocr)
    assert val_ocr == "14.5 g/dL"

    # Regression: real methodology word "Hemoglobin Colorimetric 14.5 g/dL"
    text_real = "Hemoglobin Colorimetric 14.5 g/dL"
    entities_real = extract_clinical_entities(text_real)
    assert entities_real.get("hemoglobin") == "14.5 g/dL"
    val_real = extract_hemoglobin(text_real)
    assert val_real == "14.5 g/dL"


def test_hba1c_prevention():
    # HbA1c should not be matched as hemoglobin
    text = "HbA1c = 6.0 %"
    entities = extract_clinical_entities(text)
    assert "hemoglobin" not in entities

    val = extract_hemoglobin(text)
    assert val is None

    # HbA2 prevention
    text2 = "Hb A2 = 2.5 %"
    entities2 = extract_clinical_entities(text2)
    assert "hemoglobin" not in entities2

    val2 = extract_hemoglobin(text2)
    assert val2 is None


def test_wbc_extraction():
    # Standard separator
    text = "WBC Count ... 10570 /cmm"
    entities = extract_clinical_entities(text)
    assert entities.get("wbc") == "10570"


def test_platelets_extraction():
    # Dash separator
    text = "Platelet Count ----- 150000 /cmm"
    entities = extract_clinical_entities(text)
    assert entities.get("platelets") == "150000"


def test_rbc_extraction():
    # Pipe separator
    text = "RBC Count | 4.79 million/cmm"
    entities = extract_clinical_entities(text)
    assert entities.get("rbc") == "4.79"


def test_ocr_noise_tolerance():
    # intermediate words, e.g. "WBC Count SF Cube cell analysis 10570"
    text = "WBC Count SF Cube cell analysis 10570"
    entities = extract_clinical_entities(text)
    assert entities.get("wbc") == "10570"

    # Messy spacing and extra characters for Platelets
    text_plt = "Platelets level (by manual method) :::::::   150000 per microliter"
    entities_plt = extract_clinical_entities(text_plt)
    assert entities_plt.get("platelets") == "150000"

    # Messy spacing and extra characters for RBC
    text_rbc = "RBC (Red Blood Cell Count) -- -- -- -- -- 4.79 million/cu mm"
    entities_rbc = extract_clinical_entities(text_rbc)
    assert entities_rbc.get("rbc") == "4.79"


def test_end_to_end_answer_generation():
    # Context containing all target laboratory results and HbA1c
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
