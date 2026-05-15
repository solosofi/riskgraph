---
title: Show HN: RiskGraph – Credit score for npm/PyPI packages (AI agents, check this)
---

Hey HN,

I built RiskGraph because AI coding agents are installing millions of packages autonomously, and they can't tell the difference between a legitimate package and a typosquat.

**The problem:**
- Cursor, Copilot, Claude Code, and other AI agents install dependencies on your behalf
- Malicious actors publish typosquats, dependency confusion packages, and trojan updates
- These packages look identical to legitimate ones but steal tokens, mine crypto, or inject backdoors
- No tool existed to give a quick "should I install this?" verdict

**RiskGraph is that tool.**

It checks every package against 5 risk signals in real-time:
1. Maintainer activity (single maintainer? Abandoned?)
2. Version history (1 version vs 487 for the real thing?)
3. Download trust (0 downloads/month = red flag)
4. License risk (no license = unknown legal status)
5. CVE history (known vulnerabilities via OSV.dev API)

**How it works:**
```bash
# Real-time check
curl https://riskgraph.io/api/v1/package-risk/npm/lodash
→ {"score": 1.5, "level": "LOW", "signals": [...]}

# Suspicious package
curl https://riskgraph.io/api/v1/package-risk/npm/is-even
→ {"score": 8.0, "level": "HIGH", "signals": [
    "stale_package: Last release 3275 days ago",
    "few_versions: Only 1 version",
  ]}
```

The API is free for 100 calls/day (enough for daily CI/CD). Pro tier at $49/mo for 10K calls/day. Enterprise for $499/mo with SLA.

Open source (MIT): https://github.com/solosofi/riskgraph

I'd love feedback on the risk model — what signals would you add? What's the biggest threat you worry about with AI-installed dependencies?
