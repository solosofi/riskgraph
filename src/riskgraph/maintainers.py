"""Maintainer trust scoring — evaluates maintainer history and patterns."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import time


@dataclass
class MaintainerProfile:
    username: str
    account_age_days: float = 0
    packages_maintained: int = 0
    total_commits: int = 0
    recent_commit_days: int = 999  # days since last commit
    is_org: bool = False
    has_2fa: bool = False  # if detectable
    email_domain: str = ""


def analyze_maintainer_risk(
    maintainers: list[MaintainerProfile],
) -> dict:
    """Analyze a list of maintainers and return risk signals.

    Returns dict with:
      - bus_factor: number of active maintainers
      - avg_account_age_days: average account age
      - max_stale_days: longest time since any maintainer committed
      - churn_risk: 0-1 score for maintainer turnover
      - single_point_of_failure: bool
    """
    if not maintainers:
        return {
            "bus_factor": 0,
            "avg_account_age_days": 0,
            "max_stale_days": 999,
            "churn_risk": 1.0,
            "single_point_of_failure": True,
            "detail": "No maintainers found — extremely risky",
        }

    active = [m for m in maintainers if m.recent_commit_days < 365]
    bus_factor = len(active)
    avg_age = sum(m.account_age_days for m in maintainers) / len(maintainers)
    max_stale = max(m.recent_commit_days for m in maintainers)
    single_point = bus_factor <= 1

    # Churn: if many maintainers are stale or accounts are young
    young_accounts = sum(1 for m in maintainers if m.account_age_days < 180)
    stale_accounts = sum(1 for m in maintainers if m.recent_commit_days > 365)
    churn_risk = (young_accounts + stale_accounts) / max(len(maintainers), 1)

    return {
        "bus_factor": bus_factor,
        "avg_account_age_days": avg_age,
        "max_stale_days": max_stale,
        "churn_risk": min(churn_risk, 1.0),
        "single_point_of_failure": single_point,
        "detail": f"{bus_factor} active maintainer(s), avg age {avg_age:.0f}d, max stale {max_stale}d",
    }


def profile_from_npm_metadata(npm_maintainer: dict) -> MaintainerProfile:
    """Convert npm registry maintainer data to MaintainerProfile."""
    return MaintainerProfile(
        username=npm_maintainer.get("name", "unknown"),
        email_domain=npm_maintainer.get("email", "").split("@")[-1] if "@" in npm_maintainer.get("email", "") else "",
        is_org=False,
    )


def profile_from_pypi_metadata(pypi_info: dict) -> list[MaintainerProfile]:
    """Extract maintainer profiles from PyPI JSON API response."""
    info = pypi_info.get("info", {})
    author = info.get("author", "")
    maintainer = info.get("maintainer", "")
    profiles = []
    if author:
        profiles.append(MaintainerProfile(username=author))
    if maintainer and maintainer != author:
        profiles.append(MaintainerProfile(username=maintainer))
    if not profiles:
        # Try author_email
        email = info.get("author_email", "") or info.get("maintainer_email", "")
        if email:
            profiles.append(MaintainerProfile(username=email.split("@")[0], email_domain=email.split("@")[-1] if "@" in email else ""))
    return profiles
