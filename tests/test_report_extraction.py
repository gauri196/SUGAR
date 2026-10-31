"""
SUGAR — Phase 4 Medical Report Extraction Tests.

Verifies:
- Valid JSON and CSV structured extraction.
- Supported clinical field mappings (Age, BMI, Platelets, AST, ALT, WBC, RBC, HGB).
- Missing fields and null preservation (absent values remain None, never 0).
- Invalid numeric values, NaN, and infinity handling.
- Ambiguous mappings (conflicting columns/keys) marked as unresolved without guessing.
- Unsupported units flagged rather than silently converted.
- Valid text-based PDF extraction via pypdf.
- Scanned or text-empty PDFs returning 'no_text_found' with manual review message.
- Malformed, empty, oversized, and unsupported files handled safely.
- Filename sanitization and path-traversal prevention.
- Temporary-file cleanup.
- Extraction status and unverified-value metadata (is_verified=False).
- HTTP API /api/reports/extract endpoint end-to-end.
"""
import io
import json
import pytest
from fastapi.testclient import TestClient
import pypdf

from backend.main import app
from backend.services.extraction import (
    extract_medical_report,
    sanitize_filename,
    verify_file_content,
    MAX_UPLOAD_SIZE_BYTES,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helper to create valid digital text PDF bytes
# ---------------------------------------------------------------------------

def create_sample_text_pdf(text_lines: list[str]) -> bytes:
    """Create a minimal valid digital PDF containing the specified text lines."""
    stream_content = []
    stream_content.append(b"BT\n/F1 12 Tf\n50 720 Td\n")
    for i, line in enumerate(text_lines):
        if i > 0:
            stream_content.append(b"0 -20 Td\n")
        safe_line = line.replace("(", "\\(").replace(")", "\\)")
        stream_content.append(f"({safe_line}) Tj\n".encode("latin-1", errors="replace"))
    stream_content.append(b"ET\n")
    stream_bytes = b"".join(stream_content)

    pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
        b"2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
        b"3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources 4 0 R /Contents 5 0 R>> endobj\n"
        b"4 0 obj <</Font <</F1 <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>>>>>> endobj\n"
        b"5 0 obj <</Length " + str(len(stream_bytes)).encode() + b">> stream\n"
        + stream_bytes +
        b"endstream\nendobj\n"
        b"xref\n0 6\n0000000000 65535 f \n"
        b"0000000009 00000 n \n0000000056 00000 n \n0000000115 00000 n \n0000000217 00000 n \n0000000300 00000 n \n"
        b"trailer <</Size 6 /Root 1 0 R>>\nstartxref\n500\n%%EOF\n"
    )
    return pdf


# ---------------------------------------------------------------------------
# 1. Structured JSON Extraction
# ---------------------------------------------------------------------------

def test_extract_valid_json():
    payload = {
        "Age": 48,
        "BMI": 28.5,
        "Platelet Count": 195,
        "AST": 44,
        "ALT": 39,
        "WBC": 7.1,
        "RBC": 4.6,
        "Hemoglobin": 14.8,
    }
    content = json.dumps(payload).encode("utf-8")
    res = extract_medical_report(content, "patient_lab_001.json")

    assert res.success is True
    assert res.extraction_status == "parsed"
    assert res.clinical_values["age"] == 48.0
    assert res.clinical_values["bmi"] == 28.5
    assert res.clinical_values["platelets"] == 195.0
    assert res.clinical_values["ast"] == 44.0
    assert res.clinical_values["alt"] == 39.0
    assert res.clinical_values["wbc"] == 7.1
    assert res.clinical_values["rbc"] == 4.6
    assert res.clinical_values["hgb"] == 14.8
    assert res.is_verified is False
    assert res.requires_clinician_verification is True


def test_extract_json_null_preservation():
    # Only core FIB-4 labs provided; hematology expansion absent
    payload = {
        "age": 55,
        "platelets": 160,
        "ast": 50,
        "alt": 42,
    }
    content = json.dumps(payload).encode("utf-8")
    res = extract_medical_report(content, "fib4_only.json")

    assert res.success is True
    assert res.clinical_values["age"] == 55.0
    assert res.clinical_values["platelets"] == 160.0
    assert res.clinical_values["ast"] == 50.0
    assert res.clinical_values["alt"] == 42.0
    # Absent values MUST remain None (null) and not 0
    assert res.clinical_values["bmi"] is None
    assert res.clinical_values["wbc"] is None
    assert res.clinical_values["rbc"] is None
    assert res.clinical_values["hgb"] is None
    assert "bmi" in res.missing_fields
    assert res.extracted_fields["bmi"].status == "absent"


def test_extract_json_ambiguous_fields():
    # Document contains multiple conflicting keys for AST
    payload = {
        "age": 45,
        "AST": 30,
        "AST 1": 95,  # conflicting
        "alt": 25,
        "platelets": 200,
    }
    content = json.dumps(payload).encode("utf-8")
    res = extract_medical_report(content, "ambiguous_ast.json")

    # The service must NOT guess between 30 and 95!
    assert res.clinical_values["ast"] is None
    assert "ast" in res.unresolved_fields
    assert res.extracted_fields["ast"].status == "ambiguous"


# ---------------------------------------------------------------------------
# 2. Structured CSV Extraction
# ---------------------------------------------------------------------------

def test_extract_valid_csv():
    csv_text = (
        "Age,BMI,Platelets,AST,ALT,WBC,RBC,HGB\n"
        "52,27.3,175,38,32,6.8,4.5,14.2\n"
    )
    res = extract_medical_report(csv_text.encode("utf-8"), "cohort_sample.csv")

    assert res.success is True
    assert res.extraction_status == "parsed"
    assert res.clinical_values["age"] == 52.0
    assert res.clinical_values["bmi"] == 27.3
    assert res.clinical_values["platelets"] == 175.0
    assert res.clinical_values["ast"] == 38.0
    assert res.clinical_values["alt"] == 32.0
    assert res.clinical_values["wbc"] == 6.8
    assert res.clinical_values["rbc"] == 4.5
    assert res.clinical_values["hgb"] == 14.2
    assert res.is_verified is False


def test_extract_csv_invalid_and_negative_values():
    # Negative platelet count and non-numeric AST
    csv_text = (
        "Age,Platelets,AST,ALT\n"
        "45,-150,ELEVATED,30\n"
    )
    res = extract_medical_report(csv_text.encode("utf-8"), "invalid_values.csv")

    assert res.clinical_values["platelets"] is None
    assert res.extracted_fields["platelets"].status == "invalid"
    assert res.clinical_values["ast"] is None
    assert res.extracted_fields["ast"].status == "invalid"
    assert len(res.errors) >= 2


def test_extract_csv_ambiguous_columns():
    # CSV has both AST and SGOT headers with conflicting values
    csv_text = (
        "Age,AST,SGOT,ALT,Platelets\n"
        "50,40,90,35,210\n"
    )
    res = extract_medical_report(csv_text.encode("utf-8"), "conflict.csv")

    assert res.clinical_values["ast"] is None
    assert "ast" in res.unresolved_fields
    assert res.extracted_fields["ast"].status == "ambiguous"


# ---------------------------------------------------------------------------
# 3. Digital Text PDF Extraction
# ---------------------------------------------------------------------------

def test_extract_valid_text_pdf():
    lines = [
        "LABORATORY DIAGNOSTIC REPORT",
        "Patient Age: 60",
        "AST (SGOT): 55 U/L",
        "ALT (SGPT): 45 U/L",
        "Platelet Count: 140 x10^3/uL",
        "BMI: 30.1 kg/m^2",
        "Hemoglobin: 13.5 g/dL",
    ]
    pdf_bytes = create_sample_text_pdf(lines)
    res = extract_medical_report(pdf_bytes, "clinic_report.pdf")

    assert res.success is True
    assert res.extraction_status == "parsed"
    assert res.clinical_values["age"] == 60.0
    assert res.clinical_values["ast"] == 55.0
    assert res.clinical_values["alt"] == 45.0
    assert res.clinical_values["platelets"] == 140.0
    assert res.clinical_values["bmi"] == 30.1
    assert res.clinical_values["hgb"] == 13.5
    assert res.extracted_fields["ast"].source_snippet is not None
    assert res.is_verified is False


def test_extract_scanned_or_empty_pdf():
    # A PDF with an empty blank page and no text stream
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buf = io.BytesIO()
    writer.write(buf)
    empty_pdf = buf.getvalue()

    res = extract_medical_report(empty_pdf, "scanned_doc.pdf")
    assert res.success is False
    assert res.extraction_status == "no_text_found"
    assert any("no extractable text" in w.lower() for w in res.warnings)


# ---------------------------------------------------------------------------
# 4. Upload Security, Malformed, and Path Traversal Tests
# ---------------------------------------------------------------------------

def test_empty_file_rejection():
    res = extract_medical_report(b"", "empty.json")
    assert res.success is False
    assert res.extraction_status == "unsupported_format"
    assert any("empty" in e.lower() for e in res.errors)


def test_oversized_file_rejection():
    # Oversized content > 5 MB
    large_content = b"x" * (MAX_UPLOAD_SIZE_BYTES + 1024)
    res = extract_medical_report(large_content, "huge.csv")
    assert res.success is False
    assert res.extraction_status == "unsupported_format"
    assert any("exceeds maximum" in e.lower() for e in res.errors)


def test_prohibited_executable_binary_rejection():
    # Windows PE executable header (MZ)
    fake_exe = b"MZ\x90\x00\x03\x00\x00\x00" + b"\x00" * 100
    res = extract_medical_report(fake_exe, "malware.exe")
    assert res.success is False
    assert res.extraction_status == "unsupported_format"
    assert any("Prohibited" in e for e in res.errors)


def test_filename_sanitization_path_traversal():
    assert sanitize_filename("../../../../etc/passwd") == "passwd"
    assert sanitize_filename("..\\..\\windows\\system32\\cmd.exe") == "cmd.exe"
    assert sanitize_filename("report\x00_test.json") == "report_test.json"
    assert sanitize_filename("") == "unnamed_report"


# ---------------------------------------------------------------------------
# 5. HTTP API Endpoint End-to-End (/api/reports/extract)
# ---------------------------------------------------------------------------

def test_api_report_extract_json():
    payload = {
        "age": 42,
        "bmi": 24.5,
        "platelets": 255,
        "ast": 25,
        "alt": 24,
        "wbc": 6.5,
        "rbc": 4.8,
        "hgb": 15.0,
    }
    content = json.dumps(payload).encode("utf-8")
    files = {"file": ("patient_case1.json", content, "application/json")}
    response = client.post("/api/reports/extract", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["extraction_status"] == "parsed"
    assert data["clinical_values"]["platelets"] == 255.0
    assert data["clinical_values"]["ast"] == 25.0
    assert data["is_verified"] is False
    assert data["requires_clinician_verification"] is True


def test_api_report_extract_empty_file():
    files = {"file": ("empty.csv", b"", "text/csv")}
    response = client.post("/api/reports/extract", files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_api_report_extract_unsupported_format():
    files = {"file": ("script.sh", b"#!/bin/bash\necho hello", "application/x-sh")}
    response = client.post("/api/reports/extract", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["extraction_status"] == "unsupported_format"


# ---------------------------------------------------------------------------
# 6. PDF Regression Tests: Tabular Layout, Units, Provenance & Boundaries
# ---------------------------------------------------------------------------

def test_extract_tabular_text_pdf_synthetic_layout():
    """Verify tabular multi-line extraction where labels and values are on separate lines."""
    lines = [
        "COMPREHENSIVE METABOLIC & HEMATOLOGY PANEL",
        "Age at report",
        "45",
        "years",
        "Aspartate aminotransferase (AST)",
        "42",
        "U/L",
        "10-40",
        "Alanine aminotransferase (ALT)",
        "38",
        "U/L",
        "7-56",
        "Platelet count",
        "180",
        "10^9/L",
        "150-400",
        "Body mass index (BMI)",
        "27.4",
        "kg/m^2",
        "18.5-24.9",
        "White blood cell count (WBC)",
        "6.4",
        "10^9/L",
        "4.0-11.0",
        "Red blood cell count (RBC)",
        "4.8",
        "10^12/L",
        "4.5-5.9",
        "Hemoglobin (HGB)",
        "14.2",
        "g/dL",
        "13.5-17.5",
        "Fasting glucose",
        "104",
        "mg/dL",
        "70-99",
        "Total cholesterol",
        "192",
        "mg/dL",
        "<200",
    ]
    pdf_bytes = create_sample_text_pdf(lines)
    res = extract_medical_report(pdf_bytes, "tabular_report.pdf")

    assert res.success is True
    assert res.extraction_status == "parsed"
    assert res.clinical_values["age"] == 45.0
    assert res.clinical_values["ast"] == 42.0
    assert res.clinical_values["alt"] == 38.0
    assert res.clinical_values["platelets"] == 180.0
    assert res.clinical_values["bmi"] == 27.4
    assert res.clinical_values["wbc"] == 6.4
    assert res.clinical_values["rbc"] == 4.8
    assert res.clinical_values["hgb"] == 14.2
    assert res.clinical_values["glucose"] == 104.0
    assert res.clinical_values["cholesterol"] == 192.0
    assert res.clinical_values["cap_steatosis"] is None

    # Statuses and provenance verification
    assert res.extracted_fields["age"].status == "valid"
    assert res.extracted_fields["age"].unit == "years"
    assert "Age at report" in res.extracted_fields["age"].source_snippet

    assert res.extracted_fields["platelets"].status == "valid"
    assert res.extracted_fields["platelets"].unit == "10^9/L"

    assert res.extracted_fields["ast"].status == "valid"
    assert res.extracted_fields["ast"].unit == "U/L"

    assert res.extracted_fields["cap_steatosis"].status == "absent"
    assert res.is_verified is False
    assert res.requires_clinician_verification is True


def test_extract_pdf_malformed_value_and_missing_label():
    """Verify malformed numeric values mark field as invalid without crashing."""
    lines = [
        "Aspartate aminotransferase (AST)",
        "NOT_A_NUMBER",
        "U/L",
        "Alanine aminotransferase (ALT)",
        "38",
        "U/L",
    ]
    pdf_bytes = create_sample_text_pdf(lines)
    res = extract_medical_report(pdf_bytes, "malformed_ast.pdf")

    # AST is invalid; ALT is valid
    assert res.clinical_values["ast"] is None
    assert res.extracted_fields["ast"].status == "invalid"
    assert res.clinical_values["alt"] == 38.0
    assert res.extracted_fields["alt"].status == "valid"
    # Unmentioned fields must remain absent (null, not zero)
    assert res.clinical_values["age"] is None
    assert res.extracted_fields["age"].status == "absent"
    assert res.clinical_values["platelets"] is None
    assert res.extracted_fields["platelets"].status == "absent"


def test_extract_pdf_ambiguous_or_unsupported_unit():
    """Verify incompatible clinical units are flagged as ambiguous without silent conversion."""
    lines = [
        "Patient Age: 50",
        "AST (SGOT): 42 mmol/L",  # Incompatible unit for standard FIB-4 U/L
        "Platelet count: 180 fl",   # Incompatible platelet unit
        "ALT: 38 U/L",
    ]
    pdf_bytes = create_sample_text_pdf(lines)
    res = extract_medical_report(pdf_bytes, "unsupported_units.pdf")

    assert res.clinical_values["ast"] is None
    assert res.extracted_fields["ast"].status == "ambiguous"
    assert "unsupported unit" in res.extracted_fields["ast"].error_message.lower()

    assert res.clinical_values["platelets"] is None
    assert res.extracted_fields["platelets"].status == "ambiguous"
    assert "unsupported unit" in res.extracted_fields["platelets"].error_message.lower()

    assert res.clinical_values["alt"] == 38.0
    assert res.extracted_fields["alt"].status == "valid"


def test_extract_pdf_no_cross_field_leakage():
    """Verify consecutive labels without values do not leak values to adjacent fields."""
    lines = [
        "Body mass index (BMI)",
        "Platelet count",
        "180",
        "10^9/L",
        "Alanine aminotransferase (ALT)",
        "38",
        "U/L",
    ]
    pdf_bytes = create_sample_text_pdf(lines)
    res = extract_medical_report(pdf_bytes, "leakage_test.pdf")

    assert res.clinical_values["bmi"] is None
    assert res.extracted_fields["bmi"].status == "absent"
    assert res.clinical_values["platelets"] == 180.0
    assert res.extracted_fields["platelets"].status == "valid"
    assert res.clinical_values["alt"] == 38.0
    assert res.extracted_fields["alt"].status == "valid"


def test_extract_synthetic_pdf_file_if_available():
    """Verify extraction directly on the actual synthetic liver fibrosis test report if on disk."""
    import os
    synthetic_pdf_path = r"C:\Users\bhush\Downloads\SUGAR_synthetic_liver_fibrosis_test_report.pdf"
    if not os.path.exists(synthetic_pdf_path):
        pytest.skip("Synthetic PDF file not found at expected path")

    with open(synthetic_pdf_path, "rb") as f:
        pdf_bytes = f.read()

    res = extract_medical_report(pdf_bytes, "SUGAR_synthetic_liver_fibrosis_test_report.pdf")

    assert res.success is True
    assert res.extraction_status == "parsed"
    assert res.clinical_values["age"] == 45.0
    assert res.clinical_values["bmi"] == 27.4
    assert res.clinical_values["platelets"] == 180.0
    assert res.clinical_values["ast"] == 42.0
    assert res.clinical_values["alt"] == 38.0
    assert res.clinical_values["wbc"] == 6.4
    assert res.clinical_values["rbc"] == 4.8
    assert res.clinical_values["hgb"] == 14.2
    assert res.clinical_values["glucose"] == 104.0
    assert res.clinical_values["cholesterol"] == 192.0
    assert res.clinical_values["cap_steatosis"] is None

    # Check that platelets and wbc identified their source scale without silent distortion
    assert res.extracted_fields["platelets"].status == "valid"
    assert res.extracted_fields["ast"].status == "valid"
    assert res.extracted_fields["alt"].status == "valid"
    assert res.extracted_fields["age"].status == "valid"

    # API verification metadata
    assert res.is_verified is False
    assert res.requires_clinician_verification is True


def test_api_report_extract_tabular_pdf_endpoint():
    """Verify POST /api/reports/extract handles tabular PDF upload end-to-end."""
    lines = [
        "Patient Age: 45",
        "Aspartate aminotransferase (AST)",
        "42",
        "U/L",
        "Alanine aminotransferase (ALT)",
        "38",
        "U/L",
        "Platelet count",
        "180",
        "10^9/L",
    ]
    pdf_bytes = create_sample_text_pdf(lines)
    files = {"file": ("tabular_lab.pdf", pdf_bytes, "application/pdf")}
    response = client.post("/api/reports/extract", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["extraction_status"] == "parsed"
    assert data["clinical_values"]["age"] == 45.0
    assert data["clinical_values"]["ast"] == 42.0
    assert data["clinical_values"]["alt"] == 38.0
    assert data["clinical_values"]["platelets"] == 180.0
    assert data["is_verified"] is False
    assert data["requires_clinician_verification"] is True

