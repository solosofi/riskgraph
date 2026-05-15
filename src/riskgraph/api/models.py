from pydantic import BaseModel, Field
class PackageRiskResponse(BaseModel):
    package: str; ecosystem: str; version: str = "latest"
    score: float = Field(..., ge=0, le=10)
    level: str; signals: list[dict] = []
class ScanRequest(BaseModel):
    packages: list[str]; ecosystem: str = "npm"
class ScanResponse(BaseModel):
    results: list[PackageRiskResponse]; scanned: int; high_risk: int
