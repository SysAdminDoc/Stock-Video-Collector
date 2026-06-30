"""Shared helpers for official stock-site API connectors."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, quote_plus, urlencode, urlparse


DEFAULT_PER_PAGE = 40
MAX_PAGE_LIMIT = 20


@dataclass
class ApiRequest:
    url: str
    headers: Dict[str, str]
    timeout: int = 20


@dataclass
class ApiResponse:
    status: int
    headers: Dict[str, str]
    data: Dict[str, Any]


@dataclass
class ApiPage:
    clips: List[Dict[str, Any]]
    next_page: Optional[int] = None
    quota_remaining: str = ""
    quota_reset: str = ""
    total: str = ""


class ApiConnectorError(Exception):
    """Raised when an official API connector cannot fetch a usable page."""


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _first_present(*values: Any) -> str:
    for value in values:
        cleaned = _clean(value)
        if cleaned:
            return cleaned
    return ""


def _join_tags(tags: Any) -> str:
    if isinstance(tags, str):
        return tags
    if isinstance(tags, list):
        out = []
        for item in tags:
            if isinstance(item, dict):
                out.append(_clean(item.get("name") or item.get("title") or item.get("tag")))
            else:
                out.append(_clean(item))
        return ", ".join(t for t in out if t)
    return ""


def _duration_seconds(value: Any) -> str:
    if value in (None, ""):
        return ""
    try:
        total = int(float(value))
    except (TypeError, ValueError):
        return _clean(value)
    if total <= 0:
        return ""
    mins, secs = divmod(total, 60)
    hours, mins = divmod(mins, 60)
    if hours:
        return f"{hours}:{mins:02d}:{secs:02d}"
    return f"{mins}:{secs:02d}"


def _resolution(width: Any, height: Any) -> str:
    try:
        w = int(width or 0)
        h = int(height or 0)
    except (TypeError, ValueError):
        return ""
    if w > 0 and h > 0:
        return f"{w}x{h}"
    return ""


def _append_query(url: str, params: Dict[str, Any]) -> str:
    clean = {k: v for k, v in params.items() if v not in (None, "")}
    if not clean:
        return url
    sep = "&" if "?" in url else "?"
    return url + sep + urlencode(clean, doseq=True)


def _query_from_url(start_url: str) -> str:
    parsed = urlparse(start_url or "")
    params = parse_qs(parsed.query)
    for key in ("query", "q", "k", "search", "term", "keywords"):
        values = params.get(key)
        if values and _clean(values[0]):
            return _clean(values[0])
    path = parsed.path.strip("/")
    if not path:
        return ""
    parts = [p for p in path.split("/") if p.lower() not in {
        "video", "videos", "stock-video", "stock-footage", "search", "channels",
    }]
    if parts:
        return parts[-1].replace("-", " ").replace("+", " ").strip()
    return ""


def query_from_config(cfg: Dict[str, Any], profile_name: str, start_url: str = "") -> str:
    slug = profile_name.lower().replace(" ", "_").replace("-", "_")
    return _first_present(
        cfg.get(f"{slug}_api_query"),
        cfg.get("api_search_query"),
        _query_from_url(start_url),
    )


def quoted_query(query: str) -> str:
    return quote_plus(query or "")


class OfficialApiConnector:
    profile_name = ""
    config_keys = ()
    default_collection = ""

    def __init__(self, cfg: Optional[Dict[str, Any]] = None):
        self.cfg = cfg or {}

    def credential(self) -> str:
        return _first_present(*(self.cfg.get(key) for key in self.config_keys))

    def is_configured(self) -> bool:
        return bool(self.credential())

    def fetch_page(self, page: int, per_page: int, query: str, http_json):
        raise NotImplementedError
