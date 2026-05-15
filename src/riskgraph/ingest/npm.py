"""npm registry API crawler — fetches package metadata, downloads, and maintainer data."""

from __future__ import annotations
import json
import time
import sqlite3
import os
from typing import Optional

import httpx

CACHE_DIR = os.path.expanduser("~/.riskgraph")
CACHE_DB = os.path.join(CACHE_DIR, "cache.db")
CACHE_TTL = 86400  # 24 hours


def _ensure_cache():
    os.makedirs(CACHE_DIR, exist_ok=True)
    conn = sqlite3.connect(CACHE_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            timestamp REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def _get_cached(key: str) -> Optional[dict]:
    _ensure_cache()
    conn = sqlite3.connect(CACHE_DB)
    row = conn.execute(
        "SELECT data, timestamp FROM cache WHERE key = ?", (key,)
    ).fetchone()
    conn.close()
    if row and (time.time() - row[1]) < CACHE_TTL:
        try:
            return json.loads(row[0])
        except json.JSONDecodeError:
            return None
    return None


def _set_cached(key: str, data: dict):
    _ensure_cache()
    conn = sqlite3.connect(CACHE_DB)
    conn.execute(
        "INSERT OR REPLACE INTO cache (key, data, timestamp) VALUES (?, ?, ?)",
        (key, json.dumps(data), time.time()),
    )
    conn.commit()
    conn.close()


NPM_REGISTRY = "https://registry.npmjs.org"
NPM_DOWNLOADS = "https://api.npmjs.org/downloads"


def fetch_package_metadata(package: str) -> Optional[dict]:
    """Fetch full package metadata from npm registry."""
    cache_key = f"npm:meta:{package}"
    cached = _get_cached(cache_key)
    if cached:
        return cached

    url = f"{NPM_REGISTRY}/{package}"
    try:
        with httpx.Client(timeout=15, follow_redirects=True) as client:
            resp = client.get(url, headers={"Accept": "application/json"})
            if resp.status_code == 200:
                data = resp.json()
                _set_cached(cache_key, data)
                return data
            elif resp.status_code == 404:
                return None
            else:
                return None
    except (httpx.HTTPError, httpx.TimeoutException):
        return None


def fetch_downloads(package: str, period: str = "month") -> Optional[dict]:
    """Fetch download counts from npm API."""
    cache_key = f"npm:downloads:{package}:{period}"
    cached = _get_cached(cache_key)
    if cached:
        return cached

    url = f"{NPM_DOWNLOADS}/point/last-{period}/{package}"
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
    """Extract key risk signals from npm package data.

    Returns a dict with all the data needed by the scorer.
    """
    meta = fetch_package_metadata(package)
    if not meta:
        return {"error": f"Package '{package}' not found on npm"}

    # Latest version info
    dist_tags = meta.get("dist-tags", {})
    latest_version = dist_tags.get("latest", "unknown")
    versions = list(meta.get("versions", {}).keys())

    # Latest version metadata
    latest_meta = meta.get("versions", {}).get(latest_version, {})

    # Maintainers
    maintainers = meta.get("maintainers", [])
    maintainer_count = len(maintainers)

    # Dependencies
    deps = latest_meta.get("dependencies", {})
    dev_deps = latest_meta.get("devDependencies", {})
    total_deps = len(deps) + len(dev_deps)

    # Time data (publishing history)
    time_data = meta.get("time", {})
    created = time_data.get("created", "")
    modified = time_data.get("modified", "")

    # Calculate account age proxy from package creation
    created_ts = 0
    if created:
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            created_ts = (time.time() - dt.timestamp()) / 86400
        except (ValueError, OSError):
            created_ts = 0

    # Recent commit proxy: days since last publish
    days_since_publish = 999
    if modified:
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(modified.replace("Z", "+00:00"))
            days_since_publish = (time.time() - dt.timestamp()) / 86400
        except (ValueError, OSError):
            pass

    # Downloads
    downloads_data = fetch_downloads(package)
    monthly_downloads = 0
    if downloads_data:
        monthly_downloads = downloads_data.get("downloads", 0)

    # Check for deprecated
    deprecated = latest_meta.get("deprecated", False)

    # License
    license_info = latest_meta.get("license", "UNKNOWN")

    # Repository
    repo = latest_meta.get("repository", {})
    repo_url = ""
    if isinstance(repo, dict):
        repo_url = repo.get("url", "")
    elif isinstance(repo, str):
        repo_url = repo

    return {
        "name": package,
        "ecosystem": "npm",
        "version": latest_version,
        "maintainer_count": maintainer_count,
        "maintainers": maintainers,
        "total_deps": total_deps,
        "dependencies": list(deps.keys()),
        "dev_dependencies": list(dev_deps.keys()),
        "versions": versions,
        "version_count": len(versions),
        "created_days_ago": created_ts,
        "days_since_publish": days_since_publish,
        "monthly_downloads": monthly_downloads,
        "deprecated": bool(deprecated),
        "license": license_info,
        "repository_url": repo_url,
    }
