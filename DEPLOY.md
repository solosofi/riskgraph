# Deployment

After `git pull`:

```bash
cd /mnt/c/Users/User/riskgraph

# Clean failed builds
docker compose down
docker compose build --no-cache
docker compose up -d

# Test
curl http://localhost:8000/api/v1/package-risk/npm/lodash

# Dashboard at: http://localhost:8080
```

## Without Docker (venv)
```bash
cd /mnt/c/Users/User/riskgraph
python3 -m venv .venv
source .venv/bin/activate
uv pip install -e .
uvicorn riskgraph.api.server:app --host 0.0.0.0 --port 8000
```

## Cloud Deploy
- **Render**: Connect repo → Deploy (free tier, auto-detects render.yaml)
- **Fly.io**: `flyctl launch` (requires fly.io account + billing)
