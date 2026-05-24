from clinical_entities import extract_clinical_entities


sample_text = """
Hemoglobin: 13.5 g/dL
Glucose: 110 mg/dL
WBC: 8500
Platelets: 250000
Creatinine: 1.1 mg/dL
"""


entities = extract_clinical_entities(sample_text)

print(entities)