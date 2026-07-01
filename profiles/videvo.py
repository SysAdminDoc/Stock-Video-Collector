"""Built-in Videvo/Magnific site profile and contract fixtures."""

PROFILE_NAME = 'Videvo'
CONTRACT = {
    'catalog_urls': [
        'https://www.videvo.net/stock-video-footage/',
        'https://www.magnific.com/videos',
    ],
    'item_urls': [
        {
            'url': 'https://www.magnific.com/free-video/group-gen-z-friends-looking-mobile-phone-with-motion-graphics-emojis-showing-multiple-social-media-notifications-liking-reacting-online-content_3445332',
            'clip_id': '3445332',
        },
    ],
    'excluded_urls': [
        'https://www.magnific.com/ai/video-generator',
        'https://www.magnific.com/pricing',
    ],
    'video_urls': [
        {'url': 'https://img.magnific.com/videos/free-video-3445332.mp4', 'allowed': True},
        {'url': 'https://www.magnific.com/ai/video-generator', 'allowed': False},
    ],
}


def build(SiteProfile):
    """Return a configured SiteProfile instance."""
    return SiteProfile(
        'Videvo',
        description='Videvo legacy route now resolves to Magnific/Freepik royalty-free video catalog',
        domains=[
            'videvo.net', 'www.videvo.net',
            'freepik.com', 'www.freepik.com',
            'magnific.com', 'www.magnific.com', 'img.magnific.com',
        ],
        start_url='https://www.magnific.com/videos',
        license_name='Magnific/Freepik free video license',
        license_url='https://www.magnific.com/terms-of-use',
        attribution_required='Required for free videos',
        terms_url='https://www.magnific.com/terms-of-use',
        preview_status='Free stock video',
        catalog_patterns=['/stock-video-footage', '/videos', '/free-videos', '/free-video'],
        item_patterns=['/free-video/'],
        exclude_patterns=[
            '/ai/', '/ai-', '/image', '/images', '/photos', '/vectors',
            '/pricing', '/enterprise', '/login', '/signup',
        ],
        item_url_regex=r'(?:magnific|freepik)\.com/free-video/[^/?#]+_(\d+)(?:[/?#]|$)',
        clip_id_regex=r'(?:magnific|freepik)\.com/free-video/[^/?#]+_(\d+)(?:[/?#]|$)',
        video_types=['mp4', 'mov', 'webm', 'm3u8'],
        scroll_items=True,
        og_fallback=True,
        jsonld_fallback=True,
    )
