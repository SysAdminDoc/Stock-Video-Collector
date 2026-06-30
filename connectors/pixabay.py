"""Official Pixabay video API connector."""

from .base import (
    ApiConnectorError,
    ApiPage,
    ApiRequest,
    OfficialApiConnector,
    _clean,
    _duration_seconds,
    _first_present,
    _resolution,
    _append_query,
)


class PixabayConnector(OfficialApiConnector):
    profile_name = "Pixabay"
    config_keys = ("pixabay_api_key",)
    default_collection = "Pixabay API"

    def fetch_page(self, page, per_page, query, http_json):
        key = self.credential()
        if not key:
            raise ApiConnectorError("Pixabay API key is not configured")
        params = {
            "key": key,
            "page": page,
            "per_page": min(int(per_page or 40), 200),
            "safesearch": "true",
        }
        if query:
            params["q"] = query
        request = ApiRequest(
            _append_query("https://pixabay.com/api/videos/", params),
            {"Accept": "application/json"},
        )
        response = http_json(request)
        if response.status == 429:
            raise ApiConnectorError("Pixabay API rate limit reached")
        if response.status >= 400:
            raise ApiConnectorError(f"Pixabay API returned HTTP {response.status}")
        data = response.data or {}
        hits = [hit for hit in data.get("hits", []) if isinstance(hit, dict)]
        clips = [self._clip(hit) for hit in hits]
        total = int(data.get("totalHits") or len(hits) or 0)
        has_next = bool(hits) and page * min(int(per_page or 40), 200) < total
        return ApiPage(
            clips=[clip for clip in clips if clip.get("clip_id")],
            next_page=page + 1 if has_next else None,
            quota_remaining=_clean(response.headers.get("X-RateLimit-Remaining")),
            quota_reset=_clean(response.headers.get("X-RateLimit-Reset")),
            total=_clean(data.get("totalHits")),
        )

    def _clip(self, item):
        file_info = self._best_video(item.get("videos", {}))
        creator = _first_present(item.get("user"), item.get("user_id"))
        return {
            "clip_id": _clean(item.get("id")),
            "source_url": _first_present(item.get("pageURL"), f"https://pixabay.com/videos/{item.get('id')}/"),
            "title": _first_present(item.get("tags"), f"Pixabay video {item.get('id')}"),
            "creator": creator,
            "collection": self.default_collection,
            "resolution": _resolution(file_info.get("width"), file_info.get("height")),
            "duration": _duration_seconds(item.get("duration")),
            "formats": "video/mp4",
            "tags": _clean(item.get("tags")),
            "m3u8_url": _clean(file_info.get("url")),
            "thumbnail_url": _first_present(file_info.get("thumbnail"), item.get("picture_id")),
            "source_site": self.profile_name,
            "attribution_text": f"Video by {creator} on Pixabay" if creator else "",
        }

    def _best_video(self, videos):
        if not isinstance(videos, dict):
            return {}
        candidates = []
        for name in ("large", "medium", "small", "tiny"):
            value = videos.get(name)
            if isinstance(value, dict) and _clean(value.get("url")):
                candidates.append(value)
        if not candidates:
            return {}
        return max(
            candidates,
            key=lambda v: int(v.get("width") or 0) * int(v.get("height") or 0),
        )
