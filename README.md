# Bloxy Nexus

Bloxy Nexus is the external AI engine behind Bloxy-bot. Base44 remains the frontend and visual layer; Render hosts this FastAPI service.

## Architecture

`Base44 (.base44.app) -> /ai/chat -> Bloxy Nexus -> 114-source registry + AI fallback -> Base44`

The registry contains 44 Render/keyed providers, 20 browser/search sources, and 50 keyless/public sources.

## Run locally

```bash
pip install -r requirements.txt
uvicorn app:app --reload
```

## Render

Use `pip install -r requirements.txt` as the build command and `uvicorn app:app --host 0.0.0.0 --port $PORT` as the start command. Put all real secrets in Render Environment Variables; never commit them.

## Base44 connection

Configure the exact Base44 origin in `BASE44_ORIGIN` when the integration is hardened. The API also permits HTTPS `*.base44.app` origins through its CORS regex so the deployed frontend can call `/ai/chat`.

## Endpoints

- `GET /health`
- `GET /ready`
- `GET /ai/providers`
- `GET /ai/providers/health`
- `POST /ai/chat`
