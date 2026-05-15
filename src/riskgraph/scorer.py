"""Core scoring engine — produces 0-10 risk scores with explainability."""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Signal:
    name: str
    raw_value: float  # 0-1 normalized
    weight: float
    contribution: float = 0.0
    detail: str = ""


@dataclass
class RiskReport:
    package: str
    ecosystem: str
    version: str = "latest"
    score: float = 0.0  # 0=safe, 10=dangerous
    level: RiskLevel = RiskLevel.LOW
    signals: list[Signal] = field(default_factory=list)
    dependencies_at_risk: int = 0
    total_dependencies: int = 0

    @property
    def score_color(self) -> str:
        if self.score <= 3.0:
            return "green"
        elif self.score <= 6.0:
            return "yellow"
        elif self.score <= 8.0:
            return "red"
        return "bold red"


# ── Default weights ──────────────────────────────────────────────────────────

DEFAULT_WEIGHTS = {
    "maintainer_trust": 0.20,
    "dependency_depth": 0.15,
    "abandoned_deps": 0.15,
    "cve_count": 0.20,
    "typosquatting": 0.10,
    "version_anomaly": 0.10,
    "download_anomaly": 0.10,
}


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def compute_maintainer_trust(
    maintainer_count: int = 1,
    avg_account_age_days: float = 365,
    recent_commit_days: int = 30,
    maintainer_churn_count: int = 0,
) -> float:
    """Return 0-1 risk signal. Higher = more risky.

    Risk increases when:
    - Few maintainers (bus factor)
    - Young accounts
    - Stale commits
    - High churn
    """
    bus_risk = 1.0 / max(maintainer_count, 1)  # 1 maintainer = 1.0 risk
    age_risk = _clamp(1.0 - (avg_account_age_days / 1460))  # <4yr = risky
    stale_risk = _clamp(recent_commit_days / 365)  # older = riskier
    churn_risk = _clamp(maintainer_churn_count / 5)
    return _clamp((bus_risk * 0.4) + (age_risk * 0.2) + (stale_risk * 0.25) + (churn_risk * 0.15))


def compute_dependency_depth_risk(
    max_depth: int = 0,
    total_deps: int = 0,
) -> float:
    """Deeper and wider dependency trees increase risk surface."""
    depth_risk = _clamp(max_depth / 12)
    width_risk = _clamp(total_deps / 200)
    return _clamp((depth_risk * 0.6) + (width_risk * 0.4))


def compute_abandoned_deps_risk(
    abandoned_count: int = 0,
    total_deps: int = 1,
) -> float:
    """Fraction of dependencies that haven't been updated in >2 years."""
    ratio = abandoned_count / max(total_deps, 1)
    return _clamp(ratio * 1.5)


def compute_cve_risk(cve_count: int = 0, critical_count: int = 0) -> float:
    """Known vulnerabilities increase risk."""
    base = _clamp(cve_count / 10)
    crit = _clamp(critical_count / 3)
    return _clamp((base * 0.5) + (crit * 0.5))


def compute_typosquatting_risk(
    is_typosquat: bool = False,
    levenshtein_dist: int = 10,
    popular_package: str = "",
) -> float:
    """Typosquatting detection — close names to popular packages."""
    if is_typosquat:
        return 1.0
    if levenshtein_dist <= 1:
        return 0.9
    if levenshtein_dist <= 2:
        return 0.6
    if levenshtein_dist <= 3:
        return 0.3
    return 0.0


def compute_version_anomaly_risk(
    version_jump_magnitude: float = 0.0,
    sudden_new_deps_count: int = 0,
    obfuscated_code_detected: bool = False,
) -> float:
    """Anomalous version patterns increase risk."""
    jump_risk = _clamp(version_jump_magnitude / 5)
    dep_risk = _clamp(sudden_new_deps_count / 5)
    obf_risk = 1.0 if obfuscated_code_detected else 0.0
    return _clamp((jump_risk * 0.3) + (dep_risk * 0.4) + (obf_risk * 0.3))


def compute_download_anomaly_risk(
    recent_avg: float = 0,
    historical_avg: float = 0,
    download_spike_ratio: float = 1.0,
) -> float:
    """Abnormal download patterns (spikes from bots, sudden drops)."""
    if historical_avg == 0:
        return 0.0
    spike_risk = _clamp((download_spike_ratio - 1) / 5)
    drop_risk = _clamp(1.0 - (recent_avg / max(historical_avg, 1)))
    return _clamp((spike_risk * 0.6) + (drop_risk * 0.4))


def score_package(
    package: str,
    ecosystem: str = "npm",
    version: str = "latest",
    maintainer_count: int = 1,
    avg_account_age_days: float = 365,
    recent_commit_days: int = 30,
    maintainer_churn_count: int = 0,
    max_dep_depth: int = 0,
    total_deps: int = 0,
    abandoned_deps: int = 0,
    cve_count: int = 0,
    critical_cves: int = 0,
    is_typosquat: bool = False,
    levenshtein_dist: int = 10,
    similar_popular: str = "",
    version_jump: float = 0.0,
    sudden_new_deps: int = 0,
    obfuscated_code: bool = False,
    recent_downloads: float = 0,
    historical_downloads: float = 0,
    download_spike_ratio: float = 1.0,
    weights: Optional[dict[str, float]] = None,
) -> RiskReport:
    """Main scoring function. Returns a RiskReport with full explainability."""

    w = {**DEFAULT_WEIGHTS, **(weights or {})}

    # Compute each signal
    signals: list[Signal] = []

    mt = compute_maintainer_trust(maintainer_count, avg_account_age_days, recent_commit_days, maintainer_churn_count)
    signals.append(Signal(
        name="maintainer_trust", raw_value=mt, weight=w["maintainer_trust"],
        detail=f"maintainers={maintainer_count}, avg_age={avg_account_age_days:.0f}d, last_commit={recent_commit_days}d, churn={maintainer_churn_count}"
    ))

    dd = compute_dependency_depth_risk(max_dep_depth, total_deps)
    signals.append(Signal(
        name="dependency_depth", raw_value=dd, weight=w["dependency_depth"],
        detail=f"max_depth={max_dep_depth}, total_deps={total_deps}"
    ))

    ad = compute_abandoned_deps_risk(abandoned_deps, total_deps)
    signals.append(Signal(
        name="abandoned_deps", raw_value=ad, weight=w["abandoned_deps"],
        detail=f"abandoned={abandoned_deps}/{total_deps}"
    ))

    cv = compute_cve_risk(cve_count, critical_cves)
    signals.append(Signal(
        name="cve_count", raw_value=cv, weight=w["cve_count"],
        detail=f"cves={cve_count}, critical={critical_cves}"
    ))

    ts = compute_typosquatting_risk(is_typosquat, levenshtein_dist, similar_popular)
    signals.append(Signal(
        name="typosquatting", raw_value=ts, weight=w["typosquatting"],
        detail=f"is_typosquat={is_typosquat}, dist={levenshtein_dist}, similar_to={similar_popular or 'none'}"
    ))

    va = compute_version_anomaly_risk(version_jump, sudden_new_deps, obfuscated_code)
    signals.append(Signal(
        name="version_anomaly", raw_value=va, weight=w["version_anomaly"],
        detail=f"jump={version_jump}, new_deps={sudden_new_deps}, obfuscated={obfuscated_code}"
    ))

    da = compute_download_anomaly_risk(recent_downloads, historical_downloads, download_spike_ratio)
    signals.append(Signal(
        name="download_anomaly", raw_value=da, weight=w["download_anomaly"],
        detail=f"recent={recent_downloads:.0f}/mo, hist={historical_downloads:.0f}/mo, spike={download_spike_ratio:.1f}x"
    ))

    # Weighted composite
    total_weight = sum(s.weight for s in signals)
    raw_score = sum(s.raw_value * s.weight for s in signals) / max(total_weight, 1e-9)

    # Scale to 0-10
    score = round(raw_score * 10, 1)

    # Determine level
    if score <= 3.0:
        level = RiskLevel.LOW
    elif score <= 6.0:
        level = RiskLevel.MEDIUM
    elif score <= 8.0:
        level = RiskLevel.HIGH
    else:
        level = RiskLevel.CRITICAL

    # Compute contributions
    for s in signals:
        s.contribution = round((s.raw_value * s.weight / max(total_weight, 1e-9)) * 10, 2)

    return RiskReport(
        package=package,
        ecosystem=ecosystem,
        version=version,
        score=score,
        level=level,
        signals=signals,
        dependencies_at_risk=abandoned_deps,
        total_dependencies=total_deps,
    )
