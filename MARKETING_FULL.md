# RiskGraph — Complete Marketing Package

## RapidAPI Listing

**Title:** RiskGraph - Credit Score for Open-Source Packages
**Tagline:** Real-time risk analysis for npm/PyPI packages
**Category:** Security / Developer Tools
**Base URL:** http://localhost:8000

**Description:**
RiskGraph analyzes open-source packages for 5 critical risk signals in real-time:

1. 🔴 CVE History — Queries the OSV.dev database for known vulnerabilities
2. 👤 Maintainer Activity — Single maintainer? Abandoned? Recent commits?
3. 📦 Version Anomalies — Suspicious version jumps? Few versions vs popular packages?
4. 📉 Download Trust — 0 downloads/month = red flag
5. ⚖️ License Risk — No license = unknown legal status

Built for AI coding agents, CI/CD pipelines, and security teams that need to verify packages before installation.

**Endpoints:**
- `GET /api/v1/package-risk/{ecosystem}/{package}` — Check a single package
- `POST /api/v1/scan` — Batch check multiple packages
- `GET /` — API health check

**Supported ecosystems:** npm, PyPI (more coming)

**Use cases:**
- AI agents checking packages before auto-installing
- CI/CD gates that block risky dependencies
- Security audits of open-source supply chain
- Developer IDE plugin integration

---

## Hacker News Post

**Title:** Show HN: RiskGraph – A credit score for npm/PyPI packages

**Body:**
AI coding agents (Cursor, Copilot, Claude Code) are now installing millions of packages autonomously. They can't tell the difference between a legitimate package and a typosquat.

RiskGraph checks every package against 5 risk signals in real-time:
- Live CVE database via OSV.dev
- Maintainer activity and version history
- Download trends
- License risk
- Version anomalies

```bash
# One API call — five risk signals
curl https://api.riskgraph.io/v1/npm/lodash
→ {"score": 1.5, "level": "LOW", "signals": [...]}
```

Open source (MIT): https://github.com/solosofi/riskgraph
Free tier: 100 calls/day

---

## Product Hunt

**Tagline:** Know every package before your AI installs it
**Description:** RiskGraph is the crash-test rating for open-source dependencies. Before your agent installs anything, it checks RiskGraph — one API call, five risk signals, zero guesswork.

---

## Social Media Posts

**Twitter/X:**
"AI agents are installing millions of npm packages autonomously. They can't spot typosquats. I built RiskGraph — a credit score for open source. One API call, 5 risk signals, real CVE data. Open source and free to start. https://github.com/solosofi/riskgraph"

**LinkedIn:**
"Supply chain attacks are rising. AI agents make it worse by auto-installing dependencies. RiskGraph checks every package for CVEs, maintainer health, version anomalies, download trust, and license risk. API-first, open source, free tier available."

**Reddit r/programming:**
"Built a credit score for npm/PyPI packages — checks CVE history, maintainer activity, version anomalies, download trust, and license risk in one API call. Open source, free tier. Thoughts? https://github.com/solosofi/riskgraph"

---

## Pricing Recommendation for RapidAPI

| Tier | Price | Quota |
|------|-------|-------|
| Free | $0 | 100 calls/day |
| Basic | $9.99/mo | 1,000 calls/day |
| Pro | $49/mo | 10,000 calls/day |
| Enterprise | Contact | Unlimited + SLA |

Or pay-per-call: $0.001/call (1/10th cent per call)
