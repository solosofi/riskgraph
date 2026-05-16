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

