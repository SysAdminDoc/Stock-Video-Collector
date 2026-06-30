"""Built-in Storyblocks site profile and contract fixtures."""

PROFILE_NAME = 'Storyblocks'
CONTRACT = {'catalog_urls': ['https://www.storyblocks.com/video/'],
 'item_urls': [{'url': 'https://www.storyblocks.com/video/stock/blue-ocean-waves-12345',
                'clip_id': '12345'}],
 'excluded_urls': ['https://www.storyblocks.com/pricing'],
 'video_urls': [{'url': 'https://cdn.storyblocks.com/video/sample/master.m3u8', 'allowed': True}]}


def build(SiteProfile):
    """Return a configured SiteProfile instance."""
    return SiteProfile(
        'Storyblocks',
        description='Storyblocks.com stock video — HLS streams',
        domains=['storyblocks.com', 'www.storyblocks.com'],
        start_url='https://www.storyblocks.com/video/',
        license_name='Storyblocks license',
        license_url='https://www.storyblocks.com/license',
        attribution_required='Per subscription license',
        terms_url='https://www.storyblocks.com/license',
        preview_status='Preview stream',
        catalog_patterns=['/video/'],
        item_patterns=['/video/stock/'],
        item_url_regex=r'/video/stock/.+',
        video_types=['m3u8', 'mp4', 'webm'],
        scroll_items=True,
        og_fallback=True,
        jsonld_fallback=True,
    )
