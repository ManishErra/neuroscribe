import sys
import os

pdf_filename = "demo_data/alex_chen_lab_report.pdf"
os.makedirs("demo_data", exist_ok=True)

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(pdf_filename, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "STERLING DIAGNOSTICS & CLINICAL LABORATORY")
    c.setFont("Helvetica", 10)
    c.drawString(50, 735, "100 Medical Center Drive, Suite 400 | Phone: (555) 019-2831")
    c.line(50, 725, 550, 725)

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 700, "PATIENT LABORATORY REPORT")

    c.setFont("Helvetica", 10)
    c.drawString(50, 680, "Patient Name: Alex Chen")
    c.drawString(250, 680, "Patient ID: AC-98412")
    c.drawString(400, 680, "Sex/Age: Male / 34Y")

    c.drawString(50, 665, "Report Date: 15-Jan-2024")
    c.drawString(250, 665, "Ordering Physician: Dr. Sarah Jenkins")
    c.drawString(400, 665, "Status: FINAL")
    c.line(50, 655, 550, 655)

    # CBC Header
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, 635, "COMPLETE BLOOD COUNT (CBC)")

    c.setFont("Helvetica-Bold", 9)
    c.drawString(50, 618, "TEST NAME")
    c.drawString(200, 618, "RESULT")
    c.drawString(280, 618, "UNITS")
    c.drawString(360, 618, "REFERENCE RANGE")
    c.drawString(480, 618, "FLAG")
    c.line(50, 612, 550, 612)

    c.setFont("Helvetica", 9)
    y = 595
    items = [
        ("Hemoglobin", "9.2", "g/dL", "13.5 - 17.5", "LOW"),
        ("RBC Count", "3.1", "M/uL", "4.5 - 5.9", "LOW"),
        ("WBC Count", "12.5", "K/uL", "4.5 - 11.0", "HIGH"),
        ("Platelets", "380", "K/uL", "150 - 450", "NORMAL"),
        ("Hematocrit", "29.5", "%", "40.0 - 50.0", "LOW"),
        ("MCV", "82.0", "fL", "83.0 - 101.0", "LOW"),
        ("MCH", "28.6", "pg", "27.1 - 32.5", "NORMAL"),
    ]

    for test, val, unit, ref, flag in items:
        c.drawString(50, y, test)
        c.drawString(200, y, val)
        c.drawString(280, y, unit)
        c.drawString(360, y, ref)
        if flag != "NORMAL":
            c.setFont("Helvetica-Bold", 9)
            c.drawString(480, y, f"* {flag} *")
            c.setFont("Helvetica", 9)
        else:
            c.drawString(480, y, flag)
        y -= 18

    # Comprehensive Metabolic Panel
    y -= 10
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "METABOLIC & BIOCHEMISTRY PANEL")
    y -= 18

    c.setFont("Helvetica-Bold", 9)
    c.drawString(50, y, "TEST NAME")
    c.drawString(200, y, "RESULT")
    c.drawString(280, y, "UNITS")
    c.drawString(360, y, "REFERENCE RANGE")
    c.drawString(480, y, "FLAG")
    c.line(50, y - 6, 550, y - 6)
    y -= 22

    c.setFont("Helvetica", 9)
    bio_items = [
        ("Fasting Blood Glucose", "141.0", "mg/dL", "70 - 99", "HIGH"),
        ("HbA1c", "7.2", "%", "< 5.7", "HIGH"),
        ("Serum Creatinine", "1.1", "mg/dL", "0.7 - 1.2", "NORMAL"),
        ("Sodium", "138", "mEq/L", "136 - 146", "NORMAL"),
        ("Potassium", "4.2", "mEq/L", "3.5 - 5.1", "NORMAL"),
    ]

    for test, val, unit, ref, flag in bio_items:
        c.drawString(50, y, test)
        c.drawString(200, y, val)
        c.drawString(280, y, unit)
        c.drawString(360, y, ref)
        if flag != "NORMAL":
            c.setFont("Helvetica-Bold", 9)
            c.drawString(480, y, f"* {flag} *")
            c.setFont("Helvetica", 9)
        else:
            c.drawString(480, y, flag)
        y -= 18

    # Notes
    y -= 15
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "PATHOLOGIST IMPRESSION & NOTES:")
    y -= 15
    c.setFont("Helvetica", 9)
    notes = [
        "1. Normocytic normochromic anemia noted with Hemoglobin 9.2 g/dL.",
        "2. Fasting glucose 141.0 mg/dL and HbA1c 7.2% indicates sub-optimal glycemic control.",
        "3. Mild leukocytosis with WBC 12.5 K/uL; clinical correlation recommended.",
    ]
    for note in notes:
        c.drawString(50, y, note)
        y -= 14

    c.save()
    print(f"PDF successfully generated at {pdf_filename}")

except Exception as e:
    print(f"Error generating PDF: {e}")
    sys.exit(1)
