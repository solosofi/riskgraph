"""Anomaly detection — typosquatting, suspicious patterns, version anomalies."""

from __future__ import annotations
from typing import Optional


# Top 50 popular npm packages (for typosquatting detection)
POPULAR_NPM = [
    "react", "lodash", "express", "axios", "moment", "typescript",
    "next", "vue", "angular", "webpack", "babel", "eslint",
    "jquery", "bootstrap", "dotenv", "chalk", "commander",
    "inquirer", "nodemon", "jest", "mocha", "underscore",
    "async", "request", "socketio", "mongoose", "prisma",
    "tailwindcss", "postcss", "vite", "rollup", "esbuild",
    "redux", "zod", "yup", "dayjs", "date-fns", "ramda",
    "rxjs", "immer", "uuid", "nanoid", "clsx",
    "classnames", "stripe", "twilio", "firebase", "supabase",
]

# Top 50 popular PyPI packages
POPULAR_PYPI = [
    "requests", "numpy", "pandas", "flask", "django", "fastapi",
    "scipy", "matplotlib", "pillow", "sqlalchemy", "celery",
    "pytest", "pyyaml", "toml", "click", "boto3", "botocore",
    "cryptography", "pyjwt", "werkzeug", "jinja2", "attrs",
    "aiohttp", "httpx", "starlette", "uvicorn", "gunicorn",
    "scikit-learn", "tensorflow", "torch", "transformers",
    "beautifulsoup4", "selenium", "playwright", "twisted",
    "paramiko", "fabric", "ansible", "kubernetes", "docker",
    "grpcio", "protobuf", "pydantic", "rich", "typer",
    "polars", "arrow", "pendulum", "cloudpickle", "dask",
]


def levenshtein_distance(s1: str, s2: str) -> int:
    """Compute Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # j+1 instead of j since previous_row and current_row are one longer
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def check_typosquatting(
    package_name: str,
    ecosystem: str = "npm",
    threshold: int = 3,
) -> dict:
    """Check if a package name is a potential typosquat of a popular package.

    Returns dict with:
      - is_typosquat: bool
      - min_distance: int (Levenshtein distance to closest popular package)
      - similar_to: str (the popular package it's closest to)
    """
    popular = POPULAR_NPM if ecosystem == "npm" else POPULAR_PYPI
    name_lower = package_name.lower().replace("-", "").replace("_", "")

    best_dist = 999
    best_match = ""

    for pop in popular:
        pop_clean = pop.lower().replace("-", "").replace("_", "")
        # Only check if similar length (skip very different lengths)
        if abs(len(name_lower) - len(pop_clean)) > 4:
            continue
        dist = levenshtein_distance(name_lower, pop_clean)
        if dist < best_dist:
            best_dist = dist
            best_match = pop

    is_typo = best_dist <= 1 and package_name.lower() not in [p.lower() for p in popular]

    return {
        "is_typosquat": is_typo,
        "min_distance": best_dist,
        "similar_to": best_match if best_dist <= threshold else "",
        "threshold": threshold,
    }


def detect_version_anomalies(versions: list[str]) -> dict:
    """Detect suspicious version patterns.

    Checks:
      - Unusual version jumps (e.g., 1.0.0 -> 5.0.0)
      - Too many versions in short time
      - Missing patch/minor versions
    """
    if len(versions) < 2:
        return {"jump_magnitude": 0.0, "suspicious": False, "detail": "Not enough versions"}

    # Parse semantic versions
    parsed = []
    for v in versions:
        v = v.lstrip("v")
        parts = v.split(".")
        try:
            major = int(parts[0])
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
            parsed.append((major, minor, patch))
        except (ValueError, IndexError):
            continue

    if len(parsed) < 2:
        return {"jump_magnitude": 0.0, "suspicious": False, "detail": "Unparseable versions"}

    # Find biggest jump
    max_jump = 0.0
    for i in range(1, len(parsed)):
        prev = parsed[i - 1]
        curr = parsed[i]
        # Major version jump is most significant
        jump = abs(curr[0] - prev[0]) * 10 + abs(curr[1] - prev[1]) * 2 + abs(curr[2] - prev[2]) * 0.5
        max_jump = max(max_jump, jump)

    # Many versions might indicate rapid changes (could be suspicious)
    version_count = len(versions)

    suspicious = max_jump >= 10 or version_count > 500

    return {
        "jump_magnitude": max_jump,
        "suspicious": suspicious,
        "version_count": version_count,
        "detail": f"max_jump={max_jump:.1f}, versions={version_count}",
    }


def detect_sudden_dependency_insertion(
    current_deps: list[str],
    previous_deps: list[str],
) -> dict:
    """Detect if new dependencies were suddenly added."""
    current_set = set(current_deps)
    previous_set = set(previous_deps)
    new_deps = current_set - previous_set
    removed_deps = previous_set - current_set

    return {
        "new_dependencies": list(new_deps),
        "removed_dependencies": list(removed_deps),
        "new_count": len(new_deps),
        "removed_count": len(removed_deps),
        "suspicious": len(new_deps) >= 3 or (len(new_deps) > 0 and len(removed_deps) > 0),
    }


def detect_download_anomaly(
    recent_downloads: float,
    historical_avg: float,
) -> dict:
    """Detect abnormal download patterns."""
    if historical_avg == 0:
        return {"spike_ratio": 1.0, "suspicious": False, "detail": "No historical data"}

    ratio = recent_downloads / max(historical_avg, 1)

    # Spikes >5x are suspicious (could be bot-driven)
    # Drops <0.3x indicate abandoned package
    suspicious = ratio > 5.0 or ratio < 0.3

    return {
        "spike_ratio": round(ratio, 2),
        "suspicious": suspicious,
        "recent_downloads": recent_downloads,
        "historical_avg": historical_avg,
        "detail": f"ratio={ratio:.1f}x recent, {'SPIKE' if ratio > 5 else 'DROP' if ratio < 0.3 else 'normal'}",
    }
