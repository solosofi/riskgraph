FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv==0.11.1

COPY pyproject.toml src/ /app/
RUN uv pip install --system -e . && rm -rf /root/.cache/uv

EXPOSE 8000

CMD ["uvicorn", "riskgraph.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
