# RiskGraph Launch Kit

## RapidAPI Listing

Title: RiskGraph - Credit Score for Open-Source Packages
Category: Security / Developer Tools
Tags: supply-chain-security, npm, pypi, cve, osv, ai-agents, devsecops
Pricing: $0.10/call; free tier 100 calls/day; Pro $49/mo for 10k calls/day.

Description:
RiskGraph analyzes open-source packages for five critical risk signals in real time: CVE history via OSV.dev, maintainer activity, version anomalies, download trust, and license risk. It is built for AI coding agents, CI/CD pipelines, and security teams that need to verify packages before installation.

Endpoints:
GET /api/v1/package-risk/{ecosystem}/{package}
POST /api/v1/scan
GET /

## Short pitch
AI agents are installing dependencies autonomously. RiskGraph gives them a package credit score before they install anything.

## Reddit/HN post
Show HN: RiskGraph – A credit score for npm/PyPI packages

AI coding agents are now installing packages autonomously. RiskGraph checks packages before install: live CVEs via OSV.dev, maintainer health, version anomalies, download trust, and license risk. Open source: https://github.com/solosofi/riskgraph
