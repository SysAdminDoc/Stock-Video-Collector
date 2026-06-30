"""Built-in Pexels site profile and contract fixtures."""

PROFILE_NAME = 'Pexels'
CONTRACT = {'catalog_urls': ['https://www.pexels.com/videos/', 'https://www.pexels.com/search/videos/ocean/'],
 'item_urls': [{'url': 'https://www.pexels.com/video/waves-on-the-beach-1234567/',
                'clip_id': '1234567'}],
 'excluded_urls': ['https://www.pexels.com/photo/sample-123/'],
 'video_urls': [{'url': 'https://videos.pexels.com/video-files/1234567/1234567-hd_1920_1080_30fps.mp4',
                 'allowed': True},
                {'url': 'https://example.com/video.mp4', 'allowed': False}]}


def build(SiteProfile):
    """Return a configured SiteProfile instance."""
    return SiteProfile(
        'Pexels',
        description='Pexels.com free stock videos — direct MP4 downloads (SD/HD/UHD)',
        domains=['pexels.com', 'www.pexels.com'],
        start_url='https://www.pexels.com/videos/',
        license_name='Pexels License',
        license_url='https://www.pexels.com/license/',
        attribution_required='No',
        terms_url='https://www.pexels.com/license/',
        preview_status='Direct MP4',
        catalog_patterns=['/videos/', '/search/videos/', '/collections/'],
        item_patterns=['/video/'],
        exclude_patterns=[
            '/download/', '/license/', '/photo/', '/ja-jp/', '/ko-kr/',
            '/de-de/', '/fr-fr/', '/es-es/', '/pt-br/', '/zh-cn/', '/zh-tw/',
            '/ru-ru/', '/it-it/', '/nl-nl/', '/pl-pl/', '/sv-se/', '/tr-tr/',
            '/da-dk/', '/fi-fi/', '/nb-no/', '/cs-cz/', '/hu-hu/', '/ro-ro/',
            '/sk-sk/', '/uk-ua/', '/vi-vn/', '/th-th/', '/el-gr/', '/et-ee/',
            '/id-id/', '/ca-es/',
        ],
        item_url_regex=r'pexels\.com/video/[^/]+-\d+/?$',
        video_types=['mp4', 'webm'],
        video_cdn_domain='videos.pexels.com',
        scroll_items=True,
        metadata_selectors={},
        og_fallback=True,
        jsonld_fallback=True,
        load_more_selector='[class*="loadMore"], [class*="LoadMore"]',
        load_more_clicks=15,
    )
