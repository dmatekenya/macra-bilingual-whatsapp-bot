from typing import Optional
import requests
from src.config import settings


def create_handoff(
    phone_number: str,
    message: str,
    name: Optional[str] = None,
    language: Optional[str] = None,
) -> bool:
    if not settings.handoff_api_url:
        return False

    payload = {
        "phone_number": phone_number,
        "name": name,
        "message": message,
        "language": language,
        "channel": "whatsapp",
    }

    headers = {}
    if settings.handoff_api_token:
        headers["Authorization"] = f"Bearer {settings.handoff_api_token}"

    response = requests.post(
        settings.handoff_api_url,
        json=payload,
        headers=headers,
        timeout=20,
    )
    response.raise_for_status()
    return True