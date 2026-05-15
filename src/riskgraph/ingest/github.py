"""GitHub API crawler — fetches repo and maintainer activity data."""

from __future__ import annotations
import json
import os
import time
from typing import Optional

import httpx

from .npm import _ensure_cache, _get_cached, _set_cached

GITHUB_API = "https://api.github.com"

# Token from environment or config
_GH_TOKEN = os.environ.get("RISKGRAPH_GH_TOKEN", "")


def _gh_headers() -> dict:
    headers = {"Accept": "application/vnd.github.v3+json"}
    if _GH_TOKEN:
        headers["Authorization"] = f"token {_GH_TOKEN}"
    return headers


def fetch_repo_info(owner: str, repo: str) -> Optional[dict]:
    """Fetch repository info from GitHub API."""
    cache_key = f"github:repo:{owner}/{repo}"
    cached = _get_cached(cache_key)
    if cached:
        return cached

    url = f"{GITHUB_API}/repos/{owner}/{repo}"
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(url, headers=_gh_headers())
            if resp.status_code == 200:
                data = resp.json()
                _set_cached(cache_key, data)
                return data
            return None
    except (httpx.HTTPError, httpx.TimeoutException):
        return None


def fetch_contributors(owner: str, repo: str) -> Optional[list[dict]]:
    """Fetch top contributors for a repo."""
    cache_key = f"github:contributors:{owner}/{repo}"
    cached = _get_cached(cache_key)
    if cached:
        return cached

    url = f"{GITHUB_API}/repos/{owner}/{repo}/contributors?per_page=10"
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(url, headers=_gh_headers())
            if resp.status_code == 200:
                data = resp.json()
                _set_cached(cache_key, data)
                return data
            return None
    except (httpx.HTTPError, httpx.TimeoutException):
        return None


def fetch_recent_commits(owner: str, repo: str, per_page: int = 5) -> Optional[list[dict]]:
    """Fetch recent commits to check activity."""
    cache_key = f"github:commits:{owner}/{repo}:{per_page}"
    cached = _get_cached(cache_key)
    if cached:
        return cached

    url = f"{GITHUB_API}/repos/{owner}/{repo}/commits?per_page={per_page}"
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(url, headers=_gh_headers())
            if resp.status_code == 200:
                data = resp.json()
                _set_cached(cache_key, data)
                return data
            return None
    except (httpx.HTTPError, httpx.TimeoutException):
        return None


def parse_repo_url(url: str) -> tuple[Optional[str], Optional[str]]:
    """Parse a GitHub repo URL into (owner, repo)."""
    if not url:
        return None, None
    # Handle various URL formats
    url = url.strip().rstrip("/")
    # https://github.com/owner/repo
    if "github.com" in url:
        parts = url.split("github.com/")[-1].split("/")
        if len(parts) >= 2:
            return parts[0], parts[1].replace(".git", "")
    # git+https://github.com/owner/repo.git
    if "github.com" in url:
        parts = url.split("github.com:")[-1].split("/") if ":" in url else url.split("github.com/")[-1].split("/")
        if len(parts) >= 2:
            return parts[0], parts[1].replace(".git", "")
    return None, None


def extract_github_signals(owner: str, repo: str) -> dict:
    """Extract risk-relevant signals from GitHub repo data."""
    repo_info = fetch_repo_info(owner, repo)
    if not repo_info:
        return {"error": f"Repo {owner}/{repo} not found"}

    # Contributors
    contributors = fetch_contributors(owner, repo) or []
    contributor_count = len(contributors)
    active_contributors = sum(1 for c in contributors if c.get("contributions", 0) > 5)

    # Recent commits
    commits = fetch_recent_commits(owner, repo) or []
    days_since_last_commit = 999
    if commits:
        try:
            commit_date = commits[0].get("commit", {}).get("author", {}).get("date", "")
            if commit_date:
                from datetime import datetime
                dt = datetime.fromisoformat(commit_date.replace("Z", "+00:00"))
                days_since_last_commit = (time.time() - dt.timestamp()) / 86400
        except (ValueError, OSError, IndexError):
            pass

    # Repo signals
    stars = repo_info.get("stargazers_count", 0)
    forks = repo_info.get("forks_count", 0)
    open_issues = repo_info.get("open_issues_count", 0)
    archived = repo_info.get("archived", False)
    is_fork = repo_info.get("fork", False)
    created_at = repo_info.get("created_at", "")
    pushed_at = repo_info.get("pushed_at", "")

    # Account age
    repo_age_days = 0
    if created_at:
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            repo_age_days = (time.time() - dt.timestamp()) / 86400
        except (ValueError, OSError):
            pass

    return {
        "owner": owner,
        "repo": repo,
        "stars": stars,
        "forks": forks,
        "open_issues": open_issues,
        "contributor_count": contributor_count,
        "active_contributors": active_contributors,
        "days_since_last_commit": int(days_since_last_commit),
        "archived": archived,
        "is_fork": is_fork,
        "repo_age_days": int(repo_age_days),
    }
