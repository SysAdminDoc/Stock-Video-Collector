"""Built-in Generic site profile and contract fixtures."""

PROFILE_NAME = 'Generic'
CONTRACT = {'catalog_urls': ['https://example.com/videos'],
 'item_urls': [{'url': 'https://example.com/videos/sample-12345', 'clip_id': '12345'}],
 'excluded_urls': ['mailto:test@example.com'],
 'video_urls': [{'url': 'https://example.com/media/sample.m3u8', 'allowed': True},
                {'url': 'https://example.com/media/sample.mov', 'allowed': True},
                {'url': 'https://example.com/media/sample.jpg', 'allowed': False}]}


def build(SiteProfile):
    """Return a configured SiteProfile instance."""
    return SiteProfile(
        'Generic',
        description='Auto-detect video streams on any site (M3U8, MP4, WebM, DASH)',
        domains=[],  # allow all
        start_url='',
        catalog_patterns=[],
        item_patterns=[],
        item_url_regex='',
        video_types=['m3u8', 'mp4', 'webm', 'mpd', 'mov'],
        scroll_items=True,
        og_fallback=True,
        jsonld_fallback=True,
    )
