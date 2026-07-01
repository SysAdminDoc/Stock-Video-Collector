"""Built-in YouTube Creative Commons profile and contract fixtures."""

PROFILE_NAME = 'YouTube CC-BY'
CONTRACT = {
    'catalog_urls': [
        'https://www.youtube.com/results?search_query=creative+commons+stock+footage',
        'https://www.youtube.com/playlist?list=PL1234567890abcdef',
    ],
    'item_urls': [
        {'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', 'clip_id': 'dQw4w9WgXcQ'},
        {'url': 'https://youtu.be/dQw4w9WgXcQ', 'clip_id': 'dQw4w9WgXcQ'},
        {'url': 'https://www.youtube.com/shorts/dQw4w9WgXcQ', 'clip_id': 'dQw4w9WgXcQ'},
    ],
    'excluded_urls': [
        'https://www.youtube.com/feed/history',
        'https://accounts.youtube.com/signin',
    ],
    'video_urls': [
        {'url': 'https://rr1---sn.example.googlevideo.com/videoplayback/sample.mp4', 'allowed': True},
        {'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', 'allowed': False},
    ],
}


def build(SiteProfile):
    """Return a configured SiteProfile instance."""
    return SiteProfile(
        'YouTube CC-BY',
        description='YouTube Creative Commons metadata ingest via yt-dlp; use yt-dlp Ingest mode instead of browser crawl',
        domains=[
            'youtube.com', 'www.youtube.com', 'm.youtube.com',
            'youtu.be', 'www.youtu.be', 'googlevideo.com',
        ],
        start_url='https://www.youtube.com/results?search_query=creative+commons+stock+footage',
        license_name='Creative Commons Attribution license',
        license_url='https://support.google.com/youtube/answer/2797468',
        attribution_required='Yes',
        terms_url='https://www.youtube.com/t/terms',
        preview_status='yt-dlp metadata ingest',
        catalog_patterns=['/results', '/playlist', '/channel/', '/c/', '/@'],
        item_patterns=['/watch', '/shorts/'],
        exclude_patterns=[
            '/feed/', '/account', '/signin', '/login', '/premium',
            '/paid_memberships', '/shopping', '/gaming',
        ],
        item_url_regex=(
            r'(?:youtube\.com/watch\?v=|youtube\.com/shorts/|youtu\.be/)'
            r'([A-Za-z0-9_-]{6,})'
        ),
        video_types=['mp4', 'webm'],
        video_cdn_domain='googlevideo.com',
        scroll_items=False,
        og_fallback=True,
        jsonld_fallback=True,
    )
