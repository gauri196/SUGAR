"""
SUGAR — Research Models (Model 3 & Model 4) Schemas.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Model 3: UCI HCV 5-Class Exploratory Classifier
# ---------------------------------------------------------------------------

class UciHcvInputSchema(BaseModel):
    age: float = Field(..., ge=1.0, le=120.0, description="Patient age in years")
    sex: str = Field(default="m", description="Biological sex ('m' or 'f')")
    alb: Optional[float] = Field(default=None, description="Albumin (g/L)")
    alp: Optional[float] = Field(default=None, description="Alkaline Phosphatase (U/L)")
    alt: Optional[float] = Field(default=None, description="ALT (U/L)")
    ast: Optional[float] = Field(default=None, description="AST (U/L)")
    bil: Optional[float] = Field(default=None, description="Total Bilirubin (μmol/L)")
    che: Optional[float] = Field(default=None, description="Cholinesterase (kU/L)")
    chol: Optional[float] = Field(default=None, description="Cholesterol (mmol/L)")
    crea: Optional[float] = Field(default=None, description="Creatinine (μmol/L)")
    ggt: Optional[float] = Field(default=None, description="Gamma-GT (U/L)")
    prot: Optional[float] = Field(default=None, description="Total Protein (g/L)")

    @field_validator("sex")
    @classmethod
    def validate_sex(cls, v: str) -> str:
        s = v.strip().lower()
        if s not in {"m", "f", "male", "female"}:
            raise ValueError("Sex must be 'm' or 'f'")
        return "m" if s in {"m", "male"} else "f"


class UciHcvPredictionResponse(BaseModel):
    model_name: str = "Model 3: UCI HCV 5-Class Classifier"
    predicted_category: str
    class_probabilities: Dict[str, float]
    top_probability: float
    is_fibrosis_or_cirrhosis: bool
    scientific_disclaimer: str
    imbalanced_class_warning: str


# ---------------------------------------------------------------------------
# Model 4: Etiology & Clinical Stigmata Classifier
# ---------------------------------------------------------------------------

class Model4InputSchema(BaseModel):
    age_years: float = Field(..., ge=18.0, le=120.0, description="Age in years")
    sex: str = Field(default="F", description="Sex ('M' or 'F')")
    bilirubin: Optional[float] = Field(default=None, description="Serum Bilirubin (mg/dL)")
    albumin: Optional[float] = Field(default=None, description="Serum Albumin (g/dL)")
    platelets: Optional[float] = Field(default=None, description="Platelet count (10^9/L)")
    sgot: Optional[float] = Field(default=None, description="SGOT / AST (U/L)")
    alk_phos: Optional[float] = Field(default=None, description="Alkaline Phosphatase (U/L)")
    copper: Optional[float] = Field(default=None, description="Serum Copper (μg/day)")
    prothrombin: Optional[float] = Field(default=None, description="Prothrombin time (seconds)")
    ascites: Optional[str] = Field(default="N", description="Ascites present ('Y' or 'N')")
    hepatomegaly: Optional[str] = Field(default="N", description="Hepatomegaly present ('Y' or 'N')")
    spiders: Optional[str] = Field(default="N", description="Spider angiomas ('Y' or 'N')")
    edema: Optional[str] = Field(default="N", description="Edema status ('N', 'S'=slight, 'Y')")

    @field_validator("sex")
    @classmethod
    def validate_sex(cls, v: str) -> str:
        s = v.strip().upper()
        return "M" if s in {"M", "MALE"} else "F"

    @field_validator("ascites", "hepatomegaly", "spiders")
    @classmethod
    def validate_binary_signs(cls, v: Optional[str]) -> str:
        if not v:
            return "N"
        s = str(v).strip().upper()
        return "Y" if s in {"Y", "YES", "TRUE", "1"} else "N"

    @field_validator("edema")
    @classmethod
    def validate_edema(cls, v: Optional[str]) -> str:
        if not v:
            return "N"
        s = str(v).strip().upper()
        if s in {"Y", "YES", "TRUE"}:
            return "Y"
        elif s in {"S", "SLIGHT"}:
            return "S"
        return "N"


class Model4PredictionResponse(BaseModel):
    model_name: str = "Model 4: Disease Etiology & Clinical Stigmata"
    prediction: int = Field(..., description="1 = Advanced Fibrosis / Cirrhosis (Stage 3-4), 0 = Early/Moderate (Stage 1-2)")
    risk_label: str
    probability: float
    stigmata_evaluated: Dict[str, str]
    dataset_provenance: str
    scientific_disclaimer: str
