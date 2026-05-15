# RiskGraph — Why AI Agents Can't Trust Package Registries

## The Problem
AI coding agents (Cursor, Copilot, Claude Code) autonomously install millions of npm/PyPI packages. They cannot distinguish legitimate packages from malicious ones.

Attackers exploit this with:
- **Typosquatting** — `lodash@1.0.0` vs `lodash@4.18.1`
- **Dependency confusion** — private package names published publicly
- **Trojan updates** — hijacked popular packages with malicious versions
- **Empty packages** — postinstall scripts that steal credentials

## The Solution: RiskGraph
A credit score for every open-source package. Before any agent installs anything:

```bash
os-risk scan @anthropic/sdk --ecosystem npm
# → Score: 0.0 (LOW) — Safe to install

os-risk scan lodash@1.0.0 --ecosystem npm
# → Score: 9.2 (CRITICAL) — 1 version vs 487 for real lodash
```

## Why Now
AI agents are becoming autonomous. They browse, install dependencies, and write code without oversight. **They need a reality check on every package.**

## The Pitch
> RiskGraph is the crash-test rating for open-source. One API call. Five risk signals. Zero guesswork.

## Monetization
| Tier | Price | Quota |
|------|-------|-------|
| Free | $0 | 100 calls/day |
| Pro | $49/mo | 10K calls/day + batch |
| Enterprise | $499/mo | Unlimited + SBOM + SLA |
| Agent Partner | Revenue share | API integration for AI agents |

## Target Users
1. AI agent developers (Cursor, Copilot, etc.)
2. DevOps/SRE teams (CI/CD gates)
3. Security engineers (supply chain monitoring)
4. Individual developers (CLI tool)
