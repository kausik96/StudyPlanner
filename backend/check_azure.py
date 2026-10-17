"""Check Azure configuration without starting FastAPI or reading task data."""

import os

import httpx
from fastapi import HTTPException

from main import validate_azure_endpoint


STATUS_HINTS = {
    400: "Check model support for chat completions and max_completion_tokens.",
    401: "Check the key belongs to this resource and API-key authentication is enabled.",
    403: "Check resource access, firewall rules, and private-network requirements.",
    404: "Check the resource endpoint, deployment name, and v1 chat-completions support.",
    429: "Check your Azure quota, available capacity, and rate limits.",
}


def main() -> int:
    names = ("AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_DEPLOYMENT")
    settings = {name: os.environ.get(name, "").strip() for name in names}
    missing = [name for name, value in settings.items() if not value]
    for name in names:
        print(f"{name}: {'set' if settings[name] else 'MISSING'}")
    if missing:
        print("FAIL: Set the missing variables in this terminal, then run again.")
        print("This script does not load .env files or inherit another terminal's settings.")
        return 1

    try:
        request_url = validate_azure_endpoint(settings["AZURE_OPENAI_ENDPOINT"])
    except HTTPException as error:
        print(f"FAIL: {error.detail}")
        return 1

    print("Configuration format OK. Sending one harmless test request (Azure charges may apply).")
    try:
        with httpx.Client(timeout=15.0, follow_redirects=False) as client:
            response = client.post(
                request_url,
                headers={"api-key": settings["AZURE_OPENAI_API_KEY"]},
                json={
                    "model": settings["AZURE_OPENAI_DEPLOYMENT"],
                    "messages": [{"role": "user", "content": "Reply with only OK."}],
                    "max_completion_tokens": 300,
                },
            )
    except httpx.TimeoutException:
        print("FAIL: Azure request timed out. Check connectivity and service availability.")
        return 1
    except httpx.RequestError:
        print("FAIL: Connection failed. Check DNS, TLS certificates, proxy, and network access.")
        return 1

    if not response.is_success:
        print(f"FAIL: Azure returned HTTP {response.status_code}.")
        print(STATUS_HINTS.get(response.status_code, "Check Azure service health and deployment compatibility."))
        # Do not print provider bodies: they can echo request data or credentials.
        return 1

    try:
        content = response.json()["choices"][0]["message"]["content"]
        if not isinstance(content, str) or not content.strip():
            raise ValueError("No text returned")
    except (ValueError, KeyError, IndexError, TypeError):
        print("FAIL: Azure responded successfully but returned no usable chat text.")
        print("Check content filters and the model's output/reasoning token requirements.")
        return 1

    print("PASS: Azure accepted the key and deployment and returned nonempty chat text.")
    print("Endpoint, authentication, and basic chat generation work from this terminal.")
    print("Restart FastAPI from this same terminal to use these settings in StudyPlanner.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
