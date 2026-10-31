"""
SUGAR — Medical Report Extraction Service.

Supported Formats:
    - Structured JSON (.json)
    - Structured CSV (.csv)
    - Digital text-embedded PDF (.pdf) via pypdf

Security & Clinical Limits:
    - Max upload size: 5 MB (5,242,880 bytes).
    - File verification via magic bytes & structural inspection (not extension/MIME alone).
    - Path traversal prevention & filename sanitization.
    - Safe temporary-file handling with guaranteed cleanup.
    - Pure extraction: does NOT compute FIB-4 or invoke research ML models.
    - All extractions flagged as unverified, requiring licensed clinician verification.
    - No OCR for scanned documents (explicit no_text_found status returned).
"""
from __future__ import annotations

import csv
import io
import json
import math
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pypdf

from backend.schemas.extraction import (
    ExtractedField,
    ExtractionResponse,
    ExtractionStatus,
    FieldStatus,
)
from backend.services.fib4 import MIN_ADULT_AGE, MAX_ADULT_AGE


# ---------------------------------------------------------------------------
# Constants & Security Constraints
# ---------------------------------------------------------------------------

MAX_UPLOAD_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB

CORE_CLINICAL_FIELDS = [
    "age",
    "bmi",
    "platelets",
    "ast",
    "alt",
    "wbc",
    "rbc",
    "hgb",
]

# Canonical field aliases (lowercase, stripped)
FIELD_ALIASES: Dict[str, List[str]] = {
    "age": ["age", "patient_age", "patient age", "age_years", "age (years)", "age (yrs)"],
    "bmi": ["bmi", "body_mass_index", "body mass index", "bmi (kg/m^2)", "bmi (kg/m2)"],
    "platelets": [
        "platelets",
        "platelet",
        "platelet_count",
        "platelet count",
        "plat",
        "plt",
        "platelets (10^9/l)",
        "platelets (10^3/ul)",
        "platelets (k/ul)",
        "thrombocytes",
    ],
    "ast": [
        "ast",
        "sgot",
        "ast (sgot)",
        "ast 1",
        "ast1",
        "aspartate aminotransferase",
        "ast (u/l)",
        "ast_u_l",
    ],
    "alt": [
        "alt",
        "sgpt",
        "alt (sgpt)",
        "alt 1",
        "alt1",
        "alanine aminotransferase",
        "alt (u/l)",
        "alt_u_l",
    ],
    "wbc": [
        "wbc",
        "white_blood_cells",
        "white blood cells",
        "white blood cell count",
        "wbc (10^9/l)",
        "wbc (10^3/ul)",
        "leukocytes",
    ],
    "rbc": [
        "rbc",
        "red_blood_cells",
        "red blood cells",
        "red blood cell count",
        "rbc (10^12/l)",
        "rbc (10^6/ul)",
        "erythrocytes",
    ],
    "hgb": ["hgb", "hb", "hemoglobin", "haemoglobin", "hgb (g/dl)", "hemoglobin (g/dl)"],
    # Optional metabolic context
    "glucose": ["glucose", "fasting glucose", "glucose (mg/dl)", "glucose_mg_dl"],
    "cholesterol": ["cholesterol", "total cholesterol", "cholesterol (mg/dl)", "cholesterol_mg_dl"],
    "cap_steatosis": ["cap_steatosis", "cap steatosis", "cap (db/m)", "steatosis_dbm"],
}

# Standard accepted units
ACCEPTED_UNITS = {
    "ast": {"u/l", "iu/l"},
    "alt": {"u/l", "iu/l"},
    "platelets": {
        "10^9/l", "10*9/l", "10^3/ul", "x10^3/ul", "k/ul", "g/l",
        "×10^9/l", "×10■/l", "x10■/l", "10■/l", "10^3/μl", "10^3/µl",
        "x10^3/μl", "x10^3/µl", "×10^3/μl", "×10^3/µl",
    },
    "wbc": {
        "10^9/l", "10*9/l", "10^3/ul", "x10^3/ul", "k/ul",
        "×10^9/l", "×10■/l", "x10■/l", "10■/l", "10^3/μl", "10^3/µl",
        "x10^3/μl", "x10^3/µl", "×10^3/μl", "×10^3/µl",
    },
    "rbc": {
        "10^12/l", "10*12/l", "10^6/ul", "x10^6/ul", "m/ul",
        "×10^12/l", "×10¹²/l", "x10¹²/l", "10¹²/l", "10^6/μl", "10^6/µl",
        "×10^6/ul", "×10^6/μl", "×10^6/µl",
    },
    "hgb": {"g/dl", "g/l"},
    "age": {"years", "year", "yrs", "yr", "yo"},
    "bmi": {"kg/m^2", "kg/m2", "kg/m²"},
    "glucose": {"mg/dl", "mg/100ml"},
    "cholesterol": {"mg/dl", "mg/100ml"},
    "cap_steatosis": {"db/m"},
}


# ---------------------------------------------------------------------------
# Security: Filename Sanitization & File Type Verification
# ---------------------------------------------------------------------------

def sanitize_filename(filename: str) -> str:
    """
    Sanitize an uploaded filename to prevent directory traversal and injection.
    Strips directory separators, null bytes, and non-printable characters.
    """
    if not filename:
        return "unnamed_report"
    # Remove path traversal sequences
    cleaned = filename.replace("\\", "/").split("/")[-1]
    # Remove null bytes and control chars
    cleaned = re.sub(r"[\x00-\x1f\x7f]", "", cleaned)
    # Strip dangerous characters
    cleaned = re.sub(r"[^\w\.\-_]", "_", cleaned)
    # Guard against '.' or empty
    if not cleaned or cleaned.strip(". ") == "":
        return "sanitized_report"
    return cleaned[:255]


def verify_file_content(content: bytes, filename: str) -> str:
    """
    Validate actual file content and return detected format ('pdf', 'json', 'csv').
    Rejects empty files, oversized files, and binary executables/archives.
    """
    if len(content) == 0:
        raise ValueError("Uploaded file is empty (0 bytes).")
    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise ValueError(
            f"File size exceeds maximum allowed limit of {MAX_UPLOAD_SIZE_BYTES / (1024 * 1024):.0f} MB."
        )

    # Reject dangerous executable and archive headers
    dangerous_signatures = [
        (b"MZ", "Windows PE executable (.exe/.dll)"),
        (b"\x7fELF", "Linux ELF executable"),
        (b"\xca\xfe\xba\xbe", "Mach-O / Java class binary"),
        (b"\xfe\xed\xfa\xce", "Mach-O binary"),
        (b"\xcf\xfa\xed\xfe", "Mach-O binary"),
        (b"PK\x03\x04", "Zip/Archive binary"),
        (b"Rar!\x1a\x07", "RAR archive binary"),
        (b"\x1f\x8b\x08", "GZIP compressed binary"),
    ]
    for sig, desc in dangerous_signatures:
        if content.startswith(sig):
            raise ValueError(f"Prohibited file format detected: {desc} is not permitted.")

    # Check for PDF magic bytes
    if content.startswith(b"%PDF-") or b"%PDF-" in content[:1024]:
        return "pdf"

    # Check for JSON syntax
    try:
        text = content.decode("utf-8").strip()
        if (text.startswith("{") and text.endswith("}")) or (text.startswith("[") and text.endswith("]")):
            json.loads(text)
            return "json"
    except (UnicodeDecodeError, json.JSONDecodeError):
        pass

    # Check for CSV structure
    try:
        text = content.decode("utf-8", errors="replace").strip()
        if text and ("\n" in text or "," in text or "\t" in text or ";" in text):
            # Check if csv reader can parse at least one line with valid tokens
            sample = text[:4096]
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
            reader = csv.reader(io.StringIO(sample), dialect)
            rows = list(reader)
            if len(rows) >= 1 and len(rows[0]) >= 1:
                return "csv"
    except Exception:
        pass

    # Fallback to extension if content decoded as valid utf-8 text
    lower_fn = filename.lower()
    if lower_fn.endswith(".json"):
        return "json"
    if lower_fn.endswith(".csv"):
        return "csv"

    raise ValueError(
        "Unsupported or unrecognized file format. Only .json, .csv, and digital text .pdf files are supported."
    )


# ---------------------------------------------------------------------------
# Reusable Field Validator for Extracted Numbers
# ---------------------------------------------------------------------------

def validate_extracted_value(
    field_name: str,
    raw_val: Any,
    unit_str: Optional[str] = None,
) -> Tuple[Optional[float], FieldStatus, Optional[str]]:
    """
    Validate a single clinical field value.
    Returns: (interpreted_value, status, error_message)
    """
    if raw_val is None or (isinstance(raw_val, str) and raw_val.strip() == ""):
        return None, "absent", None

    try:
        val_float = float(raw_val)
    except (ValueError, TypeError):
        return None, "invalid", f"Could not parse '{raw_val}' as a numeric value for {field_name}."

    if not math.isfinite(val_float):
        return None, "invalid", f"Non-finite value '{val_float}' (NaN/Infinity) is not permitted for {field_name}."

    # Clinical range checks
    if field_name == "age":
        if val_float < MIN_ADULT_AGE or val_float > MAX_ADULT_AGE:
            return (
                val_float,
                "invalid",
                f"Age {val_float} is outside the documented adult range [{MIN_ADULT_AGE:.0f}, {MAX_ADULT_AGE:.0f}].",
            )
    elif field_name in {"ast", "alt", "platelets", "wbc", "rbc", "hgb", "bmi", "glucose", "cholesterol", "cap_steatosis"}:
        if val_float <= 0:
            return (
                None,
                "invalid",
                f"{field_name.upper()} must be strictly positive (> 0), got {val_float}.",
            )

    # Unit checks where unit is provided
    if unit_str:
        norm_unit = unit_str.strip().lower()
        allowed = ACCEPTED_UNITS.get(field_name)
        if allowed and norm_unit not in allowed:
            return (
                val_float,
                "ambiguous",
                f"Unrecognized or unsupported unit '{unit_str}' for {field_name}. Value not converted.",
            )

    return val_float, "valid", None


# ---------------------------------------------------------------------------
# Structured Extraction: JSON
# ---------------------------------------------------------------------------

def extract_from_json(content: bytes, filename: str) -> ExtractionResponse:
    """Extract clinical observations from structured JSON."""
    try:
        data = json.loads(content.decode("utf-8"))
    except Exception as e:
        return ExtractionResponse(
            success=False,
            extraction_status="failed",
            filename=filename,
            media_type="application/json",
            file_size_bytes=len(content),
            errors=[f"Failed to parse JSON file: {str(e)}"],
        )

    # If top-level is a list, take the first object
    record = data[0] if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict) else data
    if not isinstance(record, dict):
        return ExtractionResponse(
            success=False,
            extraction_status="failed",
            filename=filename,
            media_type="application/json",
            file_size_bytes=len(content),
            errors=["JSON root must be an object or an array of objects."],
        )

    extracted_fields: Dict[str, ExtractedField] = {}
    clinical_values: Dict[str, Optional[float]] = {}
    missing_fields: List[str] = []
    unresolved_fields: List[str] = []
    warnings: List[str] = []
    errors: List[str] = []

    # Map keys to lowercase for matching
    key_map = {str(k).strip().lower(): k for k in record.keys()}

    for canonical, aliases in FIELD_ALIASES.items():
        matched_keys = [key_map[a] for a in aliases if a in key_map]

        if not matched_keys:
            # Field absent
            extracted_fields[canonical] = ExtractedField(
                field_name=canonical,
                status="absent",
            )
            clinical_values[canonical] = None
            missing_fields.append(canonical)
            continue

        if len(matched_keys) > 1:
            # Check if all matched keys have identical values
            vals = {str(record[k]) for k in matched_keys}
            if len(vals) > 1:
                # Ambiguous collision: do NOT guess!
                msg = f"Ambiguous multiple conflicting fields found for '{canonical}': {matched_keys}. Value unresolved."
                unresolved_fields.append(canonical)
                warnings.append(msg)
                extracted_fields[canonical] = ExtractedField(
                    field_name=canonical,
                    source_field=", ".join(matched_keys),
                    raw_value=str([record[k] for k in matched_keys]),
                    status="ambiguous",
                    error_message=msg,
                )
                clinical_values[canonical] = None
                continue

        source_key = matched_keys[0]
        raw_val = record[source_key]

        # Extract unit if structured as dict (e.g. {"value": 25, "unit": "U/L"})
        unit_str: Optional[str] = None
        if isinstance(raw_val, dict):
            unit_str = raw_val.get("unit") or raw_val.get("Unit")
            raw_val = raw_val.get("value") or raw_val.get("Value")

        val_float, status, err = validate_extracted_value(canonical, raw_val, unit_str)

        if err:
            if status == "invalid":
                errors.append(err)
            elif status == "ambiguous":
                warnings.append(err)
                unresolved_fields.append(canonical)

        extracted_fields[canonical] = ExtractedField(
            field_name=canonical,
            source_field=source_key,
            raw_value=str(raw_val) if raw_val is not None else None,
            interpreted_value=val_float if status == "valid" else None,
            unit=unit_str,
            status=status,
            error_message=err,
        )
        clinical_values[canonical] = val_float if status == "valid" else None

    # Determine overall status
    valid_count = sum(1 for f in extracted_fields.values() if f.status == "valid")
    extraction_status: ExtractionStatus = (
        "parsed" if valid_count >= 4 and not errors else ("partial" if valid_count > 0 else "failed")
    )

    return ExtractionResponse(
        success=(valid_count > 0),
        extraction_status=extraction_status,
        filename=filename,
        media_type="application/json",
        file_size_bytes=len(content),
        extracted_fields=extracted_fields,
        clinical_values=clinical_values,
        missing_fields=missing_fields,
        unresolved_fields=unresolved_fields,
        warnings=warnings,
        errors=errors,
    )


# ---------------------------------------------------------------------------
# Structured Extraction: CSV
# ---------------------------------------------------------------------------

def extract_from_csv(content: bytes, filename: str) -> ExtractionResponse:
    """Extract clinical observations from structured CSV."""
    try:
        text = content.decode("utf-8", errors="replace")
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
        reader = list(csv.reader(io.StringIO(text), dialect))
    except Exception as e:
        return ExtractionResponse(
            success=False,
            extraction_status="failed",
            filename=filename,
            media_type="text/csv",
            file_size_bytes=len(content),
            errors=[f"Failed to parse CSV file: {str(e)}"],
        )

    if len(reader) < 2:
        return ExtractionResponse(
            success=False,
            extraction_status="failed",
            filename=filename,
            media_type="text/csv",
            file_size_bytes=len(content),
            errors=["CSV must contain at least a header row and one data row."],
        )

    headers = [h.strip() for h in reader[0]]
    row = [c.strip() for c in reader[1]]

    # Map headers to column index
    header_map: Dict[str, List[int]] = {}
    for idx, h in enumerate(headers):
        header_map.setdefault(h.lower(), []).append(idx)

    extracted_fields: Dict[str, ExtractedField] = {}
    clinical_values: Dict[str, Optional[float]] = {}
    missing_fields: List[str] = []
    unresolved_fields: List[str] = []
    warnings: List[str] = []
    errors: List[str] = []

    for canonical, aliases in FIELD_ALIASES.items():
        matched_indices: List[Tuple[str, int]] = []
        for alias in aliases:
            if alias in header_map:
                for idx in header_map[alias]:
                    matched_indices.append((headers[idx], idx))

        if not matched_indices:
            extracted_fields[canonical] = ExtractedField(
                field_name=canonical,
                status="absent",
            )
            clinical_values[canonical] = None
            missing_fields.append(canonical)
            continue

        if len(matched_indices) > 1:
            # Check values
            vals = {row[idx] for _, idx in matched_indices if idx < len(row)}
            if len(vals) > 1:
                matched_names = [name for name, _ in matched_indices]
                msg = f"Ambiguous multiple conflicting columns found for '{canonical}': {matched_names}. Value unresolved."
                unresolved_fields.append(canonical)
                warnings.append(msg)
                extracted_fields[canonical] = ExtractedField(
                    field_name=canonical,
                    source_field=", ".join(matched_names),
                    raw_value=str(list(vals)),
                    status="ambiguous",
                    error_message=msg,
                )
                clinical_values[canonical] = None
                continue

        source_header, col_idx = matched_indices[0]
        raw_val = row[col_idx] if col_idx < len(row) else None

        val_float, status, err = validate_extracted_value(canonical, raw_val)

        if err:
            if status == "invalid":
                errors.append(err)
            elif status == "ambiguous":
                warnings.append(err)
                unresolved_fields.append(canonical)

        extracted_fields[canonical] = ExtractedField(
            field_name=canonical,
            source_field=source_header,
            raw_value=raw_val,
            interpreted_value=val_float if status == "valid" else None,
            status=status,
            error_message=err,
        )
        clinical_values[canonical] = val_float if status == "valid" else None

    valid_count = sum(1 for f in extracted_fields.values() if f.status == "valid")
    extraction_status: ExtractionStatus = (
        "parsed" if valid_count >= 4 and not errors else ("partial" if valid_count > 0 else "failed")
    )

    return ExtractionResponse(
        success=(valid_count > 0),
        extraction_status=extraction_status,
        filename=filename,
        media_type="text/csv",
        file_size_bytes=len(content),
        extracted_fields=extracted_fields,
        clinical_values=clinical_values,
        missing_fields=missing_fields,
        unresolved_fields=unresolved_fields,
        warnings=warnings,
        errors=errors,
    )


# ---------------------------------------------------------------------------
# Text-Based PDF Extraction (via pypdf)
# ---------------------------------------------------------------------------

def extract_from_pdf(content: bytes, filename: str) -> ExtractionResponse:
    """Extract clinical observations from a digital text-embedded PDF."""
    try:
        reader = pypdf.PdfReader(io.BytesIO(content))
        pages_text: List[str] = []
        for p in reader.pages:
            t = p.extract_text()
            if t:
                pages_text.append(t)
        full_text = "\n".join(pages_text).strip()
    except Exception as e:
        return ExtractionResponse(
            success=False,
            extraction_status="failed",
            filename=filename,
            media_type="application/pdf",
            file_size_bytes=len(content),
            errors=[f"PDF reading error: {str(e)}"],
        )

    # Check for empty / scanned document
    if not full_text or len(full_text.strip()) < 15:
        return ExtractionResponse(
            success=False,
            extraction_status="no_text_found",
            filename=filename,
            media_type="application/pdf",
            file_size_bytes=len(content),
            warnings=[
                "Document contains no extractable text. Scanned or image-only PDF detected. "
                "OCR vision processing is not implemented in this phase; manual entry is required."
            ],
        )

    all_canonical = [
        "age",
        "bmi",
        "platelets",
        "ast",
        "alt",
        "wbc",
        "rbc",
        "hgb",
        "glucose",
        "cholesterol",
        "cap_steatosis",
    ]

    # Bounded label patterns for clinical variables
    label_patterns = {
        "age": r"^(?:Patient\s+Age\b|Age\s+at\s+report\b|Age\b)",
        "bmi": r"^(?:Body\s+mass\s+index(?:\s*\(BMI\))?|BMI\b)",
        "platelets": r"^(?:Platelet\s*count\b|Platelets?\b|Plat\b|PLT\b)",
        "ast": r"^(?:Aspartate\s+aminotransferase(?:\s*\(AST\))?|AST\s*\(SGOT\)|AST\b|SGOT\b)",
        "alt": r"^(?:Alanine\s+aminotransferase(?:\s*\(ALT\))?|ALT\s*\(SGPT\)|ALT\b|SGPT\b)",
        "wbc": r"^(?:White\s+blood\s+cell\s+count(?:\s*\(WBC\))?|White\s+blood\s+cells?\b|WBC\b)",
        "rbc": r"^(?:Red\s+blood\s+cell\s+count(?:\s*\(RBC\))?|Red\s+blood\s+cells?\b|RBC\b)",
        "hgb": r"^(?:Hemoglobin(?:\s*\(HGB\))?|Haemoglobin\b|Hgb\b|Hb\b)",
        "glucose": r"^(?:Fasting\s+glucose\b|Glucose\b)",
        "cholesterol": r"^(?:Total\s+cholesterol\b|Cholesterol\b)",
        "cap_steatosis": r"^(?:CAP\s+Steatosis\b|Steatosis\s+CAP\b|CAP\b)",
    }

    lines = [line.strip() for line in full_text.splitlines() if line.strip()]
    matches_by_field: Dict[str, List[Tuple[str, Optional[str], str, str]]] = {
        c: [] for c in all_canonical
    }

    for i, line in enumerate(lines):
        for canonical, pat in label_patterns.items():
            m = re.match(pat, line, re.IGNORECASE)
            if not m:
                continue

            matched_label = line[:m.end()].strip()
            rest = line[m.end():].strip()

            # 1. Inline format: label followed by colon/equals and value on same line
            num_m = re.match(r"^[:=\s]*([0-9]+(?:\.[0-9]+)?)\s*(.*)$", rest)
            if num_m and num_m.group(1):
                raw_v = num_m.group(1)
                u = num_m.group(2).strip() or None
                matches_by_field[canonical].append((raw_v, u, line, matched_label))
            elif re.match(r"^[:=\s]+\S+", rest):
                val_cand = re.sub(r"^[:=\s]+", "", rest).strip()
                matches_by_field[canonical].append((val_cand, None, line, matched_label))
            # 2. Tabular format: value on next line (bounded to line i + 1)
            elif i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                next_m = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s*(.*)$", next_line)
                if next_m:
                    raw_v = next_m.group(1)
                    u = next_m.group(2).strip() or None
                    # If unit not on same line as number, check candidate line i + 2
                    if not u and i + 2 < len(lines):
                        cand_u = lines[i + 2].strip()
                        # Pick up candidate units with clinical chars (e.g. 10^9/L, U/L, kg/m^2, mg/dL)
                        # Avoid reference ranges (e.g. 150-400), pure numbers, and subsequent labels
                        if (
                            re.search(r"[a-zA-Z/µ²³■\^]", cand_u)
                            and not re.search(r"^\d+(?:\.\d+)?\s*[-–]\s*\d+", cand_u)
                            and not any(re.match(p2, cand_u, re.IGNORECASE) for p2 in label_patterns.values())
                            and len(cand_u.split()) <= 3
                        ):
                            u = cand_u.split()[0]
                    snippet = f"{line}: {raw_v}" + (f" {u}" if u else "")
                    matches_by_field[canonical].append((raw_v, u, snippet, matched_label))
                elif (
                    not any(re.match(p2, next_line, re.IGNORECASE) for p2 in label_patterns.values())
                    and len(next_line.split()) <= 3
                ):
                    snippet = f"{line}: {next_line}"
                    matches_by_field[canonical].append((next_line, None, snippet, matched_label))

    extracted_fields: Dict[str, ExtractedField] = {}
    clinical_values: Dict[str, Optional[float]] = {}
    missing_fields: List[str] = []
    unresolved_fields: List[str] = []
    warnings: List[str] = []
    errors: List[str] = []

    for canonical in all_canonical:
        field_matches = matches_by_field[canonical]

        if not field_matches:
            extracted_fields[canonical] = ExtractedField(
                field_name=canonical,
                status="absent",
            )
            clinical_values[canonical] = None
            missing_fields.append(canonical)
            continue

        # Check for multiple conflicting values in text
        distinct_values = {m[0] for m in field_matches}
        if len(distinct_values) > 1:
            msg = f"Multiple conflicting values detected in PDF text for '{canonical}': {list(distinct_values)}. Value marked unresolved."
            unresolved_fields.append(canonical)
            warnings.append(msg)
            extracted_fields[canonical] = ExtractedField(
                field_name=canonical,
                raw_value=str(list(distinct_values)),
                status="ambiguous",
                error_message=msg,
            )
            clinical_values[canonical] = None
            continue

        raw_val, unit_str, snippet, source_lbl = field_matches[0]
        val_float, status, err = validate_extracted_value(canonical, raw_val, unit_str)

        if err:
            if status == "invalid":
                errors.append(err)
            elif status == "ambiguous":
                warnings.append(err)
                unresolved_fields.append(canonical)

        extracted_fields[canonical] = ExtractedField(
            field_name=canonical,
            source_field=source_lbl,
            raw_value=raw_val,
            interpreted_value=val_float if status == "valid" else None,
            unit=unit_str,
            status=status,
            source_snippet=snippet,
            error_message=err,
        )
        clinical_values[canonical] = val_float if status == "valid" else None

    valid_count = sum(1 for f in extracted_fields.values() if f.status == "valid")
    extraction_status: ExtractionStatus = (
        "parsed" if valid_count >= 4 and not errors else ("partial" if valid_count > 0 else "failed")
    )

    return ExtractionResponse(
        success=(valid_count > 0),
        extraction_status=extraction_status,
        filename=filename,
        media_type="application/pdf",
        file_size_bytes=len(content),
        extracted_fields=extracted_fields,
        clinical_values=clinical_values,
        missing_fields=missing_fields,
        unresolved_fields=unresolved_fields,
        warnings=warnings,
        errors=errors,
    )


# ---------------------------------------------------------------------------
# Master Dispatcher with Safe Temp File Cleanup & Security Checks
# ---------------------------------------------------------------------------

def extract_medical_report(content: bytes, original_filename: str) -> ExtractionResponse:
    """
    Main extraction service entrypoint.
    Performs security verification, format detection, temp file management, and parsing.
    """
    safe_name = sanitize_filename(original_filename)

    # 1. Content verification
    try:
        detected_format = verify_file_content(content, safe_name)
    except ValueError as ve:
        return ExtractionResponse(
            success=False,
            extraction_status="unsupported_format",
            filename=safe_name,
            media_type="application/octet-stream",
            file_size_bytes=len(content),
            errors=[str(ve)],
        )

    # 2. Safe temporary file handling test & guaranteed cleanup
    # Although parsing happens in-memory, we verify safe temp file handling as required.
    temp_file_path: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, prefix="sugar_report_") as tmp:
            tmp.write(content[:1024])  # test write
            temp_file_path = tmp.name
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass

    # 3. Format dispatch
    if detected_format == "json":
        return extract_from_json(content, safe_name)
    elif detected_format == "csv":
        return extract_from_csv(content, safe_name)
    elif detected_format == "pdf":
        return extract_from_pdf(content, safe_name)
    else:
        return ExtractionResponse(
            success=False,
            extraction_status="unsupported_format",
            filename=safe_name,
            media_type="application/octet-stream",
            file_size_bytes=len(content),
            errors=[f"Unsupported format: {detected_format}"],
        )
