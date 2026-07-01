"""Built-in Videezy site profile and contract fixtures."""

PROFILE_NAME = 'Videezy'
CONTRACT = {
    'catalog_urls': [
        'https://www.videezy.com/newest',
        'https://www.videezy.com/popular',
    ],
    'item_urls': [
        {
            'url': 'https://www.videezy.com/abstract/56876-rorschach-test-ink-blots-dinosaur',
            'clip_id': '56876',
        },
    ],
    'excluded_urls': [
        'https://www.videezy.com/deals',
        'https://www.videezy.com/login',
    ],
    'video_urls': [
        {'url': 'https://static.videezy.com/system/resources/previews/000/056/876/original/sample.mp4', 'allowed': True},
        {'url': 'https://www.vecteezy.com/video/sample.mp4', 'allowed': False},
    ],
}


def build(SiteProfile):
    """Return a configured SiteProfile instance."""
    return SiteProfile(
        'Videezy',
        description='Videezy free HD and 4K stock-footage catalog',
        domains=['videezy.com', 'www.videezy.com', 'static.videezy.com'],
        start_url='https://www.videezy.com/newest',
        license_name='Videezy per-item license',
        license_url='https://www.videezy.com/terms',
        attribution_required='Per item license',
        terms_url='https://www.videezy.com/terms',
        preview_status='Free stock footage',
        catalog_patterns=['/newest', '/popular', '/category', '/search'],
        item_patterns=['/abstract/', '/backgrounds/', '/nature/', '/people/', '/technology/'],
        exclude_patterns=[
            '/vectors', '/photos', '/deals', '/join-pro', '/login',
            '/sign-up', '/support', '/dmca',
        ],
        item_url_regex=r'videezy\.com/[A-Za-z0-9-]+/(\d+)-[^/?#]+(?:[/?#]|$)',
        clip_id_regex=r'videezy\.com/[A-Za-z0-9-]+/(\d+)-[^/?#]+(?:[/?#]|$)',
        video_types=['mp4', 'webm', 'mov', 'm3u8'],
        video_cdn_domain='videezy.com',
        scroll_items=True,
        og_fallback=True,
        jsonld_fallback=True,
    )
