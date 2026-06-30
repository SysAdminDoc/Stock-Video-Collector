"""Built-in Pixabay site profile and contract fixtures."""

PROFILE_NAME = 'Pixabay'
CONTRACT = {'catalog_urls': ['https://pixabay.com/videos/'],
 'item_urls': [{'url': 'https://pixabay.com/videos/ocean-sea-waves-12345/', 'clip_id': '12345'}],
 'excluded_urls': ['https://pixabay.com/accounts/login/'],
 'video_urls': [{'url': 'https://cdn.pixabay.com/video/2024/01/clip-12345.mp4', 'allowed': True}]}


def build(SiteProfile):
    """Return a configured SiteProfile instance."""
    return SiteProfile(
        'Pixabay',
        description='Pixabay.com free stock videos',
        domains=['pixabay.com', 'www.pixabay.com'],
        start_url='https://pixabay.com/videos/',
        license_name='Pixabay Content License',
        license_url='https://pixabay.com/service/license-summary/',
        attribution_required='No',
        terms_url='https://pixabay.com/service/license-summary/',
        preview_status='Direct preview',
        catalog_patterns=['/videos/'],
        item_patterns=['/videos/'],
        item_url_regex=r'/videos/[^/]+-\d+/?$',
        video_types=['mp4', 'webm'],
        scroll_items=True,
        og_fallback=True,
        jsonld_fallback=True,
    )
