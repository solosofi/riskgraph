"""FastAPI server — serves the risk scoring API and CORS for dashboard."""

from __future__ import annotations
from typing import Optional

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from riskgraph.scorer import score_package
from riskgraph.ingest import npm, pypi
from riskgraph.anomalies import check_typosquatting

app = FastAPI(
    title="RiskGraph API",
    description="Credit Score for Open-Source Packages",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class PackageRiskResponse(BaseModel):
    package: str
    ecosystem: str
    version: str
    score: float = Field(..., ge=0, le=10)
    level: str
    signals: list[dict]
    typosquatting: dict

class ScanRequest(BaseModel):
    packages: list[str]
    ecosystem: str = "npm"

class ScanResponse(BaseModel):
    results: list[PackageRiskResponse]
    scanned_count: int
    high_risk_count: int

_FREE_TIER = 3
_usage: dict[str, int] = {}

def _check_rate(api_key: str | None) -> int:
    key = api_key or "anonymous"
    used = _usage.get(key, 0)
    return max(0, _FREE_TIER - used)

def _bump(api_key: str | None):
    key = api_key or "anonymous"
    _usage[key] = _usage.get(key, 0) + 1

def _score_one(package: str, ecosystem: str) -> PackageRiskResponse:
    info = (npm.extract_package_info(package) if ecosystem == "npm" else pypi.extract_package_info(package))
    if "error" in info:
        raise HTTPException(status_code=404, detail=info["error"])
    typo = check_typosquatting(package, ecosystem)
    report = score_package(
        package=package, ecosystem=ecosystem, version=info.get("version", "latest"),
        maintainer_count=info.get("maintainer_count", 1),
        avg_account_age_days=info.get("created_days_ago", 365),
        recent_commit_days=info.get("days_since_publish", 30),
        total_deps=info.get("total_deps", 0),
        abandoned_deps=1 if info.get("days_since_publish", 0) > 730 else 0,
        is_typosquat=typo["is_typosquat"], levenshtein_dist=typo["min_distance"],
        similar_popular=typo["similar_to"],
        recent_downloads=info.get("monthly_downloads", 0),
        historical_downloads=info.get("monthly_downloads", 0),
    )
    return PackageRiskResponse(
        package=report.package, ecosystem=report.ecosystem, version=report.version,
        score=report.score, level=report.level.value,
        signals=[{"name": s.name, "contribution": s.contribution, "detail": s.detail} for s in report.signals],
        typosquatting=typo,
    )

@app.get("/api/v1/package-risk/{ecosystem}/{package}")
def get_package_risk(ecosystem: str, package: str, api_key: Optional[str] = Header(None, alias="x-api-key")):
    if _check_rate(api_key) <= 0:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Upgrade your plan.")
    _bump(api_key)
    return _score_one(package, ecosystem)

@app.post("/api/v1/scan")
def scan_packages(req: ScanRequest, api_key: Optional[str] = Header(None, alias="x-api-key")):
    rem = _check_rate(api_key)
    if rem < len(req.packages):
        raise HTTPException(status_code=429, detail=f"Quota: {rem} left, {len(req.packages)} requested")
    results, high = [], 0
    for pkg in req.packages[:rem]:
        try:
            r = _score_one(pkg, req.ecosystem)
            _bump(api_key)
            if r.score >= 6: high += 1
            results.append(r)
        except HTTPException:
            pass
    return ScanResponse(results=results, scanned_count=len(results), high_risk_count=high)

@app.get("/api/v1/status")
def api_status():
    return {"status": "ok", "version": "0.1.0", "trial_call_limit": _FREE_TIER, "pricing": "$0.10/call via marketplace"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("riskgraph.api.server:app", host="0.0.0.0", port=8000)
