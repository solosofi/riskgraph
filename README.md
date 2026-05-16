# RiskGraph

> **Credit score for open-source packages.**  
> Know what you're installing before you install it.

RiskGraph analyzes npm and PyPI packages for risk signals: maintainer churn, version anomalies, missing licenses, abandoned dependencies, and typosquatting.

## Quick Start

```bash
pip install riskgraph
```

Scan a package:
```bash
os-risk scan lodash --ecosystem npm
```

## API

```bash
curl https://api.riskgraph.io/api/v1/package-risk/npm/lodash
```

Response:
```json
{"package": "lodash", "score": 1.1, "level": "LOW", "signals": [...]}
```

## Dashboard

[riskgraph.io](https://riskgraph.io) — input a package name, get a risk score.

## Why RiskGraph?

- **Proactive risk** — not just CVEs, but maintainer health, version anomalies, typosquatting signals
- **Ecosystem-agnostic** — npm, PyPI, GitHub
- **Developer-first** — CLI, API, dashboard, all free tier
- **Open-source** — MIT License

## Roadmap

- [x] Core scoring engine (npm, PyPI)
- [x] REST API (FastAPI)
- [x] CLI tool
- [x] Dashboard
- [ ] CI/CD integrations (GitHub Actions, GitLab)
- [ ] Enterprise SBOM generation
- [ ] Real-time package monitoring
- [ ] Data moat: 10M+ packages indexed

## License

MIT


## Monetized API

RiskGraph is designed as a paid API for AI agents and CI/CD pipelines. Recommended RapidAPI pricing:

- Free: 100 calls/day
- Usage-based: $0.10 per call
- Pro: $49/month for 10,000 calls/day
- Enterprise: custom SLA + unlimited volume

Core endpoint:

```http
GET /api/v1/package-risk/{ecosystem}/{package}
```

Example use cases: autonomous coding agents checking dependencies before install, CI dependency gates, security audits, and package reputation scoring.


## Public Deployment for RapidAPI

RapidAPI cannot call `localhost`; deploy RiskGraph first and use the public URL as the RapidAPI base URL.

Fastest options:

### Render

1. Connect this repository to Render.
2. Render auto-detects `render.yaml`.
3. Public base URL target: `https://riskgraph.onrender.com`.

### Railway

1. Connect this repository to Railway.
2. Railway uses `railway.toml`.
3. Set start command if needed:
   `uvicorn riskgraph.api.main:app --host 0.0.0.0 --port $PORT`

### RapidAPI

Use `RAPIDAPI.md` and `openapi.yaml` for the listing. Recommended monetization:

- Free: 100 calls/day
- Usage: $0.10/call
- Pro: $49/month for 10,000 calls/day
