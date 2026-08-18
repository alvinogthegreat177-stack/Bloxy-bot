import os
import httpx
from providers import ALL_PROVIDERS

async def check_env_providers():
    """Reports configuration presence without exposing secret values."""
    return {p["name"]: bool(os.getenv(p["env"])) if p["env"] else None for p in ALL_PROVIDERS}

async def check_url(url: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(url)
            return response.status_code < 500
    except Exception:
        return False
