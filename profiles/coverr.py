"""Built-in Coverr site profile and contract fixtures."""

PROFILE_NAME = 'Coverr'
CONTRACT = {
    'catalog_urls': [
        'https://coverr.co/videos',
        'https://coverr.co/videos/categories/nature',
    ],
    'item_urls': [
        {'url': 'https://coverr.co/videos/a-road-through-the-hills', 'clip_id': 'a-road-through-the-hills'},
    ],
    'excluded_urls': [
        'https://coverr.co/pricing',
        'https://coverr.co/music',
    ],
    'video_urls': [
        {'url': 'https://cdn.coverr.co/videos/coverr-a-road-through-the-hills-1080p.mp4', 'allowed': True},
        {'url': 'https://www.istockphoto.com/video/sample.mp4', 'allowed': False},
    ],
}


def build(SiteProfile):
    """Return a configured SiteProfile instance."""
    return SiteProfile(
        'Coverr',
        description='Coverr royalty-free stock-video previews and downloads',
        domains=['coverr.co', 'www.coverr.co', 'cdn.coverr.co', 'videos.coverr.co'],
        start_url='https://coverr.co/videos',
        license_name='Coverr license',
        license_url='https://coverr.co/license',
        attribution_required='No',
        terms_url='https://coverr.co/terms-of-use',
        preview_status='Royalty-free preview',
        catalog_patterns=['/videos', '/categories', '/collections', '/scenes'],
        item_patterns=['/videos/'],
        exclude_patterns=[
            '/music', '/images', '/ai-', '/pricing', '/api', '/developers',
            '/blog', '/faq', '/about', '/advertise', '/contribute',
        ],
        item_url_regex=r'coverr\.co/videos/([A-Za-z0-9-]+)(?:[/?#]|$)',
        video_types=['mp4', 'webm', 'm3u8', 'mov'],
        video_cdn_domain='coverr.co',
        scroll_items=True,
        og_fallback=True,
        jsonld_fallback=True,
    )
