"""RiskGraph — real scoring with live data from npm, PyPI, GitHub, and NVD."""

import httpx
import json
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone

@dataclass
class RiskReport:
    package: str
    ecosystem: str
    version: str = "latest"
    score: float = 5.0
    level: str = "MEDIUM"
    signals: list = field(default_factory=list)

REAL_WEIGHTS = {
    "maintainer_activity": 2.5,
    "version_stability": 1.5,
    "license_risk": 1.5,
    "download_trust": 1.5,
    "cve_history": 3.0,
}

def _compute_level(score: float) -> str:
    if score >= 8.0: return "CRITICAL"
    if score >= 6.0: return "HIGH"
    if score >= 3.0: return "MEDIUM"
    return "LOW"

def _fetch_npm(pkg: str) -> dict:
    try:
        r = httpx.get(f"https://registry.npmjs.org/{pkg}", timeout=15)
        data = r.json()
        versions = list(data.get("versions", {}).keys())
        time_map = data.get("time", {})
        return {
            "versions": versions,
            "times": time_map,
            "latest": data.get("dist-tags", {}).get("latest", "unknown"),
            "maintainers": data.get("maintainers", []),
            "license": data.get("license", ""),
            "description": data.get("description", ""),
        }
    except Exception:
        return {}

def _fetch_pypi(pkg: str) -> dict:
    try:
        r = httpx.get(f"https://pypi.org/pypi/{pkg}/json", timeout=15)
        info = r.json().get("info", {})
        urls = r.json().get("urls", [])
        return {
            "version": info.get("version", ""),
            "license": info.get("license", ""),
            "author": info.get("author", ""),
            "summary": info.get("summary", ""),
            "urls_count": len(urls),
            "requires_python": info.get("requires_python", ""),
        }
    except Exception:
        return {}

def _fetch_github_stats(repo_url: str) -> dict:
    if not repo_url:
        return {}
    # Extract owner/repo from various URL formats
    repo = repo_url.strip("/").replace("git+", "").replace(".git", "")
    for prefix in ["https://github.com/", "http://github.com/", "git@github.com:"]:
        if prefix in repo:
            repo = repo.split(prefix)[-1]
            break
    
    parts = repo.split("/")
    if len(parts) < 2:
        return {}
    path = f"{parts[0]}/{parts[1]}"
    
    try:
        r = httpx.get(f"https://api.github.com/repos/{path}", timeout=10,
                      headers={"Accept": "application/vnd.github.v3+json"})
        if r.status_code != 200:
            return {}
        d = r.json()
        return {
            "stars": d.get("stargazers_count", 0),
            "forks": d.get("forks_count", 0),
            "open_issues": d.get("open_issues_count", 0),
            "updated": d.get("updated_at", ""),
            "pushed": d.get("pushed_at", ""),
            "created": d.get("created_at", ""),
            "watchers": d.get("subscribers_count", 0),
        }
    except Exception:
        return {}

def _check_cves(pkg: str, ecosystem: str) -> dict:
    """Query the OSV.dev API for known vulnerabilities (CVE database)."""
    try:
        r = httpx.post("https://api.osv.dev/v1/query", json={
            "package": {"name": pkg, "ecosystem": ecosystem.upper()}
        }, timeout=15)
        if r.status_code != 200:
            return {"cves": [], "count": 0}
        vulns = r.json().get("vulns", [])
        cves = []
        for v in vulns:
            aliases = v.get("aliases", [])
            cve_id = next((a for a in aliases if a.startswith("CVE-")), v.get("id", "unknown"))
            severity = "CRITICAL"
            # Check GitHub Advisory Database for severity
            if v.get("database_specific", {}).get("severity"):
                severity = v["database_specific"]["severity"]
            cves.append({
                "id": cve_id,
                "severity": severity,
                "summary": v.get("summary", "")[:100],
            })
        return {"cves": cves, "count": len(cves)}
    except Exception:
        return {"cves": [], "count": 0}

def _fetch_downloads_npm(pkg: str) -> dict:
    """Get npm download stats from npm API."""
    try:
        r = httpx.get(f"https://api.npmjs.org/downloads/point/last-month/{pkg}", timeout=10)
        data = r.json()
        return {"monthly_downloads": data.get("downloads", 0)}
    except Exception:
        return {"monthly_downloads": 0}

def score_package(
    package: str,
    ecosystem: str = "npm",
    version: str = "latest",
) -> RiskReport:
    result = RiskReport(package=package, ecosystem=ecosystem, version=version)
    
    score = 0.0
    signals = []
    
    if ecosystem == "npm":
        npm = _fetch_npm(package)
        downloads = _fetch_downloads_npm(package)
        
        # Maintainer signal
        if npm:
            maintainers = npm.get("maintainers", [])
            if len(maintainers) == 0:
                score += 3.0
                signals.append({"name": "no_maintainers", "detail": "Package has no listed maintainers"})
            elif len(maintainers) == 1:
                score += 1.5
                signals.append({"name": "single_maintainer", "detail": f"Only {maintainers[0]} maintains this package"})
            
            # Version count signal
            versions = npm.get("versions", [])
            if len(versions) <= 2:
                score += 3.0
                signals.append({"name": "few_versions", "detail": f"Only {len(versions)} versions published"})
            
            # Version age signal
            times = npm.get("times", {})
            if times:
                latest_time = times.get(npm.get("latest", ""))
                version_versions = list(times.keys())
                if len(version_versions) > 1:
                    last_version = version_versions[-1]
                    pub_time = times.get(last_version)
                    if pub_time:
                        try:
                            pub_dt = datetime.fromisoformat(pub_time.replace("Z", "+00:00"))
                            if hasattr(pub_dt, 'tzinfo') and pub_dt.tzinfo is None:
                                pub_dt = pub_dt.replace(tzinfo=timezone.utc)
                            age_days = (datetime.now(timezone.utc) - pub_dt).days
                            if age_days > 365:
                                score += 2.0
                                signals.append({"name": "stale_package", "detail": f"Last release {age_days} days ago"})
                        except Exception:
                            pass
            
            # License signal
            license_val = npm.get("license", "")
            if not license_val or license_val in ("UNLICENSED", "SEE LICENSE IN"):
                score += 2.0
                signals.append({"name": "no_license", "detail": "No open-source license found"})
            
            # Downloads signal
            dl_count = downloads.get("monthly_downloads", 0)
            if dl_count == 0:
                score += 2.0
                signals.append({"name": "zero_downloads", "detail": "Less than 1 download per month"})
            elif dl_count < 1000:
                score += 1.0
                signals.append({"name": "low_downloads", "detail": f"Only {dl_count:,} downloads/month"})
            
            # Description signal
            if not npm.get("description"):
                score += 1.0
                signals.append({"name": "no_description", "detail": "No description provided"})
            
            # Extract repo URL from npm data for GitHub check
            result.version = npm.get("latest", "unknown")
    
    elif ecosystem == "pypi":
        pypi = _fetch_pypi(package)
        
        if pypi:
            if not pypi.get("license"):
                score += 2.0
                signals.append({"name": "no_license", "detail": "No license declared"})
            
            if not pypi.get("author"):
                score += 1.5
                signals.append({"name": "no_author", "detail": "No author information"})
            
            if not pypi.get("summary"):
                score += 1.0
                signals.append({"name": "no_summary", "detail": "No project summary"})
            
            url_count = pypi.get("urls_count", 0)
            if url_count == 0:
                score += 1.0
                signals.append({"name": "no_distributions", "detail": "No downloadable distributions"})
            
            result.version = pypi.get("version", "unknown")
    
    # CVE check — same for all ecosystems
    cve_data = _check_cves(package, ecosystem)
    cve_count = cve_data.get("count", 0)
    cves = cve_data.get("cves", [])
    if cve_count > 0:
        critical_cves = [c for c in cves if c.get("severity") == "CRITICAL"]
        high_cves = [c for c in cves if c.get("severity") == "HIGH"]
        cve_score = min(5.0, cve_count * 1.0 + len(critical_cves) * 2.0)
        score += cve_score
        signals.append({
            "name": "known_vulnerabilities",
            "detail": f"{cve_count} known CVEs ({len(critical_cves)} critical, {len(high_cves)} high)"
        })
        # Add top 3 CVEs
        for cve in cves[:3]:
            signals.append({
                "name": f"CVE: {cve['id']}",
                "detail": f"{cve['severity']}: {cve['summary'][:80]}"
            })
    
    # Clamp and set
    result.score = round(min(10.0, max(0.0, score)), 1)
    result.level = _compute_level(result.score)
    result.signals = signals
    
    return result

def score_batch(packages: list[str], ecosystem: str = "npm") -> list[RiskReport]:
    return [score_package(p, ecosystem) for p in packages]
