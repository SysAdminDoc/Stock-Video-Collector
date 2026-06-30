"""Official Adobe Stock search API connector."""

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


class AdobeStockConnector(OfficialApiConnector):
    profile_name = "Adobe Stock"
    config_keys = ("adobe_stock_api_key", "adobe_api_key")
    default_collection = "Adobe Stock API"

    def access_token(self):
        return _first_present(self.cfg.get("adobe_stock_access_token"), self.cfg.get("adobe_access_token"))

    def fetch_page(self, page, per_page, query, http_json):
        api_key = self.credential()
        if not api_key:
            raise ApiConnectorError("Adobe Stock API key is not configured")
        params = {
            "locale": self.cfg.get("adobe_stock_locale") or "en_US",
            "search_parameters[limit]": min(int(per_page or 40), 100),
            "search_parameters[offset]": max(page - 1, 0) * min(int(per_page or 40), 100),
            "search_parameters[filters][content_type:video]": 1,
            "result_columns[]": [
                "id", "title", "creator_name", "thumbnail_url", "content_url",
                "details_url", "duration", "width", "height", "keywords",
            ],
        }
        if query:
            params["search_parameters[words]"] = query
        headers = {
            "x-api-key": api_key,
            "x-product": "Stock-Video-Collector/desktop",
            "Accept": "application/json",
        }
        token = self.access_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        request = ApiRequest(
            _append_query("https://stock.adobe.io/Rest/Media/1/Search/Files", params),
            headers,
        )
        response = http_json(request)
        if response.status == 429:
            raise ApiConnectorError("Adobe Stock API rate limit reached")
        if response.status >= 400:
            raise ApiConnectorError(f"Adobe Stock API returned HTTP {response.status}")
        data = response.data or {}
        files = [item for item in data.get("files", []) if isinstance(item, dict)]
        clips = [self._clip(item, query) for item in files]
        total = int(data.get("nb_results") or data.get("total") or len(files) or 0)
        limit = min(int(per_page or 40), 100)
        has_next = bool(files) and page * limit < total
        return ApiPage(
            clips=[clip for clip in clips if clip.get("clip_id")],
            next_page=page + 1 if has_next else None,
            quota_remaining=_clean(response.headers.get("X-RateLimit-Remaining")),
            quota_reset=_clean(response.headers.get("X-RateLimit-Reset")),
            total=_clean(total),
        )

    def _clip(self, item, query):
        clip_id = _clean(item.get("id") or item.get("content_id"))
        return {
            "clip_id": clip_id,
            "source_url": _first_present(
                item.get("details_url"),
                item.get("content_url"),
                f"https://stock.adobe.com/video/{clip_id}",
            ),
            "title": _first_present(item.get("title"), f"Adobe Stock video {clip_id}"),
            "creator": _clean(item.get("creator_name")),
            "collection": self.default_collection,
            "resolution": _resolution(item.get("width"), item.get("height")),
            "duration": _duration_seconds(item.get("duration")),
            "formats": _first_present(item.get("media_type"), "video"),
            "tags": _join_tags(item.get("keywords")) or query or "",
            "m3u8_url": _clean(item.get("content_url") or item.get("preview_url")),
            "thumbnail_url": _first_present(item.get("thumbnail_url"), item.get("thumbnail")),
            "source_site": self.profile_name,
            "preview_status": "Watermarked preview",
        }
