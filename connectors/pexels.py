"""Official Pexels video API connector."""

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


class PexelsConnector(OfficialApiConnector):
    profile_name = "Pexels"
    config_keys = ("pexels_api_key", "pexels_access_token")
    default_collection = "Pexels API"

    def fetch_page(self, page, per_page, query, http_json):
        key = self.credential()
        if not key:
            raise ApiConnectorError("Pexels API key is not configured")
        endpoint = "https://api.pexels.com/v1/videos/search" if query else "https://api.pexels.com/v1/videos/popular"
        params = {"page": page, "per_page": min(int(per_page or 40), 80)}
        if query:
            params["query"] = query
        request = ApiRequest(
            _append_query(endpoint, params),
            {"Authorization": key, "Accept": "application/json"},
        )
        response = http_json(request)
        if response.status == 429:
            raise ApiConnectorError("Pexels API rate limit reached")
        if response.status >= 400:
            raise ApiConnectorError(f"Pexels API returned HTTP {response.status}")
        data = response.data or {}
        clips = [self._clip(hit, query) for hit in data.get("videos", []) if isinstance(hit, dict)]
        return ApiPage(
            clips=[clip for clip in clips if clip.get("clip_id")],
            next_page=page + 1 if data.get("next_page") and clips else None,
            quota_remaining=_clean(response.headers.get("X-Ratelimit-Remaining")),
            quota_reset=_clean(response.headers.get("X-Ratelimit-Reset")),
            total=_clean(data.get("total_results")),
        )

    def _clip(self, item, query):
        file_info = self._best_video_file(item.get("video_files", []))
        user = item.get("user") if isinstance(item.get("user"), dict) else {}
        creator = _first_present(user.get("name"), user.get("url"))
        width = file_info.get("width") or item.get("width")
        height = file_info.get("height") or item.get("height")
        source_url = _first_present(item.get("url"), f"https://www.pexels.com/video/{item.get('id')}/")
        title = _first_present(item.get("alt"), item.get("title"), f"Pexels video {item.get('id')}")
        return {
            "clip_id": _clean(item.get("id")),
            "source_url": source_url,
            "title": title,
            "creator": creator,
            "collection": self.default_collection,
            "resolution": _resolution(width, height),
            "duration": _duration_seconds(item.get("duration")),
            "formats": _clean(file_info.get("file_type") or "video/mp4"),
            "tags": query or "",
            "m3u8_url": _clean(file_info.get("link")),
            "thumbnail_url": _first_present(item.get("image"), self._first_picture(item.get("video_pictures", []))),
            "source_site": self.profile_name,
            "attribution_text": f"Video by {creator} on Pexels" if creator else "",
        }

    def _best_video_file(self, files):
        candidates = [f for f in files if isinstance(f, dict) and _clean(f.get("link"))]
        if not candidates:
            return {}
        mp4 = [f for f in candidates if "mp4" in _clean(f.get("file_type")).lower()]
        candidates = mp4 or candidates
        return max(
            candidates,
            key=lambda f: int(f.get("width") or 0) * int(f.get("height") or 0),
        )

    def _first_picture(self, pictures):
        for picture in pictures or []:
            if isinstance(picture, dict) and _clean(picture.get("picture")):
                return _clean(picture.get("picture"))
        return ""
