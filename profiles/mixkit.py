"""Built-in Mixkit site profile and contract fixtures."""

PROFILE_NAME = 'Mixkit'
CONTRACT = {
    'catalog_urls': [
        'https://mixkit.co/free-stock-video/',
        'https://mixkit.co/free-stock-video/nature/',
    ],
    'item_urls': [
        {
            'url': 'https://mixkit.co/free-stock-video/going-down-a-curved-highway-through-a-mountain-range-41576/',
            'clip_id': '41576',
        },
    ],
    'excluded_urls': [
        'https://mixkit.co/free-stock-music/',
        'https://mixkit.co/free-sound-effects/',
    ],
    'video_urls': [
        {'url': 'https://assets.mixkit.co/videos/preview/mixkit-curved-highway-41576-large.mp4', 'allowed': True},
        {'url': 'https://elements.envato.com/sample.mp4', 'allowed': False},
    ],
}


def build(SiteProfile):
    """Return a configured SiteProfile instance."""
    return SiteProfile(
        'Mixkit',
        description='Mixkit free stock-video clips with license and technical metadata',
        domains=['mixkit.co', 'www.mixkit.co', 'assets.mixkit.co'],
        start_url='https://mixkit.co/free-stock-video/',
        license_name='Mixkit Stock Video Free License',
        license_url='https://mixkit.co/license/#videoFree',
        attribution_required='No',
        terms_url='https://mixkit.co/terms/',
        preview_status='Free stock video',
        catalog_patterns=['/free-stock-video', '/free-stock-video/'],
        item_patterns=['/free-stock-video/'],
        exclude_patterns=[
            '/free-stock-music', '/free-sound-effects', '/templates',
            '/icons', '/premiere-pro', '/after-effects', '/final-cut-pro',
            '/davinci-resolve',
        ],
        item_url_regex=r'mixkit\.co/free-stock-video/[^/?#]+-(\d+)(?:[/?#]|$)',
        clip_id_regex=r'mixkit\.co/free-stock-video/[^/?#]+-(\d+)(?:[/?#]|$)',
        video_types=['mp4', 'webm', 'm3u8', 'mov'],
        video_cdn_domain='mixkit.co',
        scroll_items=True,
        og_fallback=True,
        jsonld_fallback=True,
    )
