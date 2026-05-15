"""Pydantic models for the RiskGraph API."""
from pydantic import BaseModel, Field
from typing import Optional

class PackageRiskResponse(BaseModel):
    package: str
    ecosystem: str
    version: str = "latest"
    score: float = Field(..., ge=0, le=10)
    level: str
    signals: list[dict] = Field(default_factory=list)

class ScanRequest(BaseModel):
    packages: list[str]
    ecosystem: str = "npm"

class ScanResponse(BaseModel):
    results: list[PackageRiskResponse]
    scanned: int
    high_risk: int
    summary: Optional[dict] = None
