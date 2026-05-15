"""PyPI API crawler — fetches package metadata, download stats, and maintainer data."""

from __future__ import annotations
import json
import time
import sqlite3
import os
from typing import Optional

import httpx

from .npm import _ensure_cache, _get_cached, _set_cached  # share cache

PYPI_JSON = "https://pypi.org/pypi"
PYPI_STATS = "https://pypistats.org/api"


def fetch_package_metadata(package: str) -> Optional[dict]:
    """Fetch full package metadata from PyPI JSON API."""
    cache_key = f"pypi:meta:{package}"
    cached = _get_cached(cache_key)
    if cached:
        return cached

    url = f"{PYPI_JSON}/{package}/json"
    try:
        with httpx.Client(timeout=15, follow_redirects=True) as client:
            resp = client.get(url, headers={"Accept": "application/json"})
            if resp.status_code == 200:
                data = resp.json()
                _set_cached(cache_key, data)
                return data
            elif resp.status_code == 404:
                return None
            return None
    except (httpx.HTTPError, httpx.TimeoutException):
        return None


def fetch_recent_downloads(package: str) -> Optional[dict]:
    """Fetch recent download stats from pypistats.org."""
    cache_key = f"pypi:stats:recent:{package}"
    cached = _get_cached(cache_key)
    if cached:
        return cached

    url = f"{PYPI_STATS}/packages/{package}/recent"
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                _set_cached(cache_key, data)
                return data
            return None
    except (httpx.HTTPError, httpx.TimeoutException):
        return None


def extract_package_info(package: str) -> dict:
    """Extract key risk signals from PyPI package data."""
    meta = fetch_package_metadata(package)
    if not meta:
        return {"error": f"Package '{package}' not found on PyPI"}

    info = meta.get("info", {})
    latest_version = info.get("version", "unknown")

    # Releases
    releases = meta.get("releases", {})
    version_list = list(releases.keys())

    # Author/maintainer
    author = info.get("author", "")
    maintainer = info.get("maintainer", "")
    maintainer_names = []
    if author:
        maintainer_names.append(author)
    if maintainer and maintainer != author:
        maintainer_names.append(maintainer)
    maintainer_count = len(maintainer_names) or 1

    # Dependencies
    requires = info.get("requires_dist", []) or []
    total_deps = len(requires)
    dep_names = []
    for r in requires:
        name = r.split(">=")[0].split("==")[0].split("<=")[0].split("~=")[0].split("!=")[0].split("[")[0].split(";")[0].strip()
        if name:
            dep_names.append(name)

    # Project URLs
    project_urls = info.get("project_urls", {}) or {}
    repo_url = project_urls.get("Source", "") or project_urls.get("Repository", "") or project_urls.get("Homepage", "")

    # License
    license_info = info.get("license", "") or "UNKNOWN"

    # Created / upload time
    urls = meta.get("urls", [])
    upload_time = ""
    if urls:
        upload_time = urls[-1].get("upload_time_iso_8641", "") or urls[-1].get("upload_time", "")

    days_since_publish = 999
    if upload_time:
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(upload_time.replace("Z", "+00:00"))
            days_since_publish = (time.time() - dt.timestamp()) / 86400
        except (ValueError, OSError):
            pass

    # Downloads
    stats = fetch_recent_downloads(package)
    recent_downloads = 0
    if stats:
        recent_downloads = stats.get("data", {}).get("last_month", 0) or 0

    # Deprecated / yanked
    yanked = any(u.get("yanked", False) for u in urls)

    return {
        "name": package,
        "ecosystem": "pypi",
        "version": latest_version,
        "maintainer_count": maintainer_count,
        "maintainers": maintainer_names,
        "total_deps": total_deps,
        "dependencies": dep_names,
        "versions": version_list,
        "version_count": len(version_list),
        "days_since_publish": days_since_publish,
        "recent_monthly_downloads": recent_downloads,
        "deprecated": yanked,
        "license": license_info,
        "repository_url": repo_url,
    }
