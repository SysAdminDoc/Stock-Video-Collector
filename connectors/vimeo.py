"""Official Vimeo API connector."""

import re

from .base import (
    ApiConnectorError,
    ApiPage,
    ApiRequest,
    OfficialApiConnector,
    _clean,
    _duration_seconds,
    _first_present,
    _join_tags,
    _resolution,
    _append_query,
)


class VimeoConnector(OfficialApiConnector):
    profile_name = "Vimeo"
    config_keys = ("vimeo_access_token", "vimeo_api_token")
    default_collection = "Vimeo API"

    def fetch_page(self, page, per_page, query, http_json):
        token = self.credential()
        if not token:
            raise ApiConnectorError("Vimeo API token is not configured")
        params = {"page": page, "per_page": min(int(per_page or 40), 100)}
        if query:
            params["query"] = query
        request = ApiRequest(
            _append_query("https://api.vimeo.com/videos", params),
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.vimeo.*+json;version=3.4",
            },
        )
        response = http_json(request)
        if response.status == 429:
            raise ApiConnectorError("Vimeo API rate limit reached")
        if response.status >= 400:
            raise ApiConnectorError(f"Vimeo API returned HTTP {response.status}")
        data = response.data or {}
        items = [item for item in data.get("data", []) if isinstance(item, dict)]
        clips = [self._clip(item, query) for item in items]
        paging = data.get("paging") if isinstance(data.get("paging"), dict) else {}
        return ApiPage(
            clips=[clip for clip in clips if clip.get("clip_id")],
            next_page=page + 1 if paging.get("next") and clips else None,
            quota_remaining=_clean(response.headers.get("X-RateLimit-Remaining")),
            quota_reset=_clean(response.headers.get("X-RateLimit-Reset")),
            total=_clean(data.get("total")),
        )

    def _clip(self, item, query):
        file_info = self._best_file(item.get("files", []))
        picture = self._best_picture(item.get("pictures"))
        user = item.get("user") if isinstance(item.get("user"), dict) else {}
        clip_id = _first_present(item.get("uri"), item.get("link"))
        id_match = re.search(r"(\d+)(?:$|[/?#])", clip_id)
        return {
            "clip_id": id_match.group(1) if id_match else _clean(clip_id),
            "source_url": _first_present(item.get("link"), f"https://vimeo.com/{clip_id.strip('/').split('/')[-1]}"),
            "title": _first_present(item.get("name"), f"Vimeo video {clip_id}"),
            "creator": _first_present(user.get("name"), user.get("link")),
            "collection": self.default_collection,
            "resolution": _resolution(file_info.get("width"), file_info.get("height")) or _resolution(item.get("width"), item.get("height")),
            "duration": _duration_seconds(item.get("duration")),
            "formats": _first_present(file_info.get("type"), file_info.get("quality")),
            "tags": _join_tags(item.get("tags")) or query or "",
            "m3u8_url": _clean(file_info.get("link")),
            "thumbnail_url": picture,
            "source_site": self.profile_name,
        }

    def _best_file(self, files):
        candidates = [f for f in files or [] if isinstance(f, dict) and _clean(f.get("link"))]
        if not candidates:
            return {}
        return max(
            candidates,
            key=lambda f: int(f.get("width") or 0) * int(f.get("height") or 0),
        )

    def _best_picture(self, pictures):
        if not isinstance(pictures, dict):
            return ""
        sizes = [s for s in pictures.get("sizes", []) if isinstance(s, dict) and _clean(s.get("link"))]
        if not sizes:
            return _clean(pictures.get("base_link"))
        best = max(sizes, key=lambda s: int(s.get("width") or 0) * int(s.get("height") or 0))
        return _clean(best.get("link"))
