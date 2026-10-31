"""
SUGAR — Medical Report Extraction Pydantic Schemas.

Defines schemas for:
- Field-level provenance and validation status.
- Structured extraction response payload.
- Human-in-the-loop clinician verification metadata.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


FieldStatus = Literal["valid", "invalid", "ambiguous", "absent"]
ExtractionStatus = Literal[
    "parsed",            # All or core fields extracted cleanly
    "partial",           # Some fields extracted; others missing or ambiguous
    "no_text_found",     # Document has no extractable text (e.g. scanned image PDF)
    "unsupported_format", # File format not recognized or disallowed
    "failed",            # Parser error or corrupt file
]


class ExtractedField(BaseModel):
    """Provenance and validation details for a single clinical observation field."""
    field_name: str = Field(..., description="Canonical clinical field name (e.g. 'platelets')")
    source_field: Optional[str] = Field(None, description="Original label/header in source file")
    raw_value: Optional[str] = Field(None, description="Raw unparsed string from document")
    interpreted_value: Optional[float] = Field(None, description="Validated numeric value, or None")
    unit: Optional[str] = Field(None, description="Extracted or recognized measurement unit")
    status: FieldStatus = Field(..., description="Validation/extraction status of this field")
    source_snippet: Optional[str] = Field(None, description="Contextual text snippet from document")
    error_message: Optional[str] = Field(None, description="Specific parsing or validation error")


class ExtractionResponse(BaseModel):
    """Complete, structured extraction result with security and verification metadata."""
    success: bool
    extraction_status: ExtractionStatus
    filename: str
    media_type: str
    file_size_bytes: int
    extracted_fields: Dict[str, ExtractedField] = Field(
        default_factory=dict,
        description="Detailed provenance for each supported clinical variable",
    )
    clinical_values: Dict[str, Optional[float]] = Field(
        default_factory=dict,
        description="Flattened canonical values ready for clinician review (preserves nulls)",
    )
    missing_fields: List[str] = Field(default_factory=list)
    unresolved_fields: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

    # Critical human verification and clinical governance attributes
    is_verified: bool = False
    requires_clinician_verification: bool = True
    verification_disclaimer: str = (
        "Extraction results are unverified automated interpretations. "
        "Values must be reviewed and confirmed by a licensed clinician before clinical use. "
        "Automated extraction does not constitute medical diagnosis or clinical decision-making."
    )
