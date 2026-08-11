from __future__ import annotations

import json
import ipaddress
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable

from .ai_generation import GenerationError

DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_USER_AGENT = "openai-python/1.0 laocaimi-content-engine/2.1"


def normalize_base_url(base_url: str | None) -> str:
    value = (base_url or DEFAULT_OPENAI_BASE_URL).strip().rstrip("/")
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        raise GenerationError("OPENAI_BASE_URL must be an absolute http(s) URL")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise GenerationError("OPENAI_BASE_URL must not contain credentials, query, or fragment")
    if parsed.scheme == "http":
        host = parsed.hostname or ""
        loopback = False
        try:
            loopback = ipaddress.ip_address(host).is_loopback
        except ValueError:
            loopback = host in {"localhost"}
        if not loopback:
            raise GenerationError("non-loopback model providers must use https")
    return value


def responses_endpoint(base_url: str | None) -> str:
    return normalize_base_url(base_url) + "/responses"


def models_endpoint(base_url: str | None) -> str:
    return normalize_base_url(base_url) + "/models"


def _redact(text: str, secret: str | None) -> str:
    if secret:
        text = text.replace(secret, "***REDACTED***")
    return text


def request_json(
    url: str,
    *,
    api_key: str,
    payload: dict | None = None,
    timeout: int = 30,
) -> dict:
    # Some OpenAI-compatible gateways apply browser/bot heuristics to the
    # default Python urllib signature. Send a stable SDK-style User-Agent and
    # explicit JSON Accept headers without weakening TLS or auth requirements.
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept-Encoding": "identity",
    }
    data = None
    method = "GET"
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        method = "POST"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = _redact(exc.read().decode("utf-8", errors="replace")[:1200], api_key)
        raise GenerationError(f"model provider HTTP {exc.code} at {url}: {detail}") from exc
    except OSError as exc:
        raise GenerationError(f"model provider transport failed at {url}: {exc}") from exc
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise GenerationError(f"model provider returned non-JSON response at {url}") from exc
    if not isinstance(result, dict):
        raise GenerationError(f"model provider returned non-object JSON at {url}")
    return result


def make_responses_transport(base_url: str | None) -> Callable[[str, dict[str, str], dict, int], dict]:
    endpoint = responses_endpoint(base_url)

    def transport(_ignored_url: str, headers: dict[str, str], payload: dict, timeout: int) -> dict:
        auth = headers.get("Authorization", "")
        prefix = "Bearer "
        if not auth.startswith(prefix) or not auth[len(prefix):]:
            raise GenerationError("missing bearer token for model provider transport")
        api_key = auth[len(prefix):]
        return request_json(endpoint, api_key=api_key, payload=payload, timeout=timeout)

    return transport
