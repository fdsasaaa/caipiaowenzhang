from __future__ import annotations

from urllib.parse import parse_qsl, urlparse

ALLOWED_SITE_HOSTS = {"laocaimi.org", "www.laocaimi.org"}


def validate_published_url(url: str, allowed_hosts: set[str] | None = None) -> str:
    allowed_hosts = set(allowed_hosts or ALLOWED_SITE_HOSTS)
    value = str(url or "").strip()
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    if parsed.scheme.lower() != "https":
        raise ValueError("published URL must use https")
    if host not in allowed_hosts:
        raise ValueError("published URL host is not allowed: " + host)
    if parsed.username or parsed.password:
        raise ValueError("published URL must not contain credentials")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("published URL has invalid port") from exc
    if port not in (None, 443):
        raise ValueError("published URL must not use a non-HTTPS port")
    if parsed.fragment:
        raise ValueError("published URL must not contain fragment")
    if not parsed.path or parsed.path == "/":
        raise ValueError("published URL must target a concrete article path")

    if parsed.query:
        if parsed.path != "/index.php":
            raise ValueError("published URL query is allowed only on the native CMS show route")
        pairs = parse_qsl(parsed.query, keep_blank_values=True, strict_parsing=True)
        if len(pairs) != 2 or len({key for key, _ in pairs}) != 2:
            raise ValueError("native CMS show URL must contain exactly c and id once")
        values = dict(pairs)
        if values.get("c") != "show" or set(values) != {"c", "id"}:
            raise ValueError("native CMS show URL must contain exactly c=show and id")
        raw_id = values.get("id", "")
        if not raw_id.isdigit() or int(raw_id) <= 0 or str(int(raw_id)) != raw_id:
            raise ValueError("native CMS show URL has invalid id")
    return value
