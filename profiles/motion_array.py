"""Built-in Motion Array site profile and contract fixtures."""

PROFILE_NAME = 'Motion Array'
CONTRACT = {'catalog_urls': ['https://motionarray.com/stock-video/'],
 'item_urls': [{'url': 'https://motionarray.com/stock-video/drone-coastline-123456/',
                'clip_id': '123456'}],
 'excluded_urls': ['https://motionarray.com/music'],
 'video_urls': [{'url': 'https://motionarray.imgix.net/preview/sample.mp4', 'allowed': True}]}


def build(SiteProfile):
    """Return a configured SiteProfile instance."""
    return SiteProfile(
        'Motion Array',
        description='Motion Array stock-video previews -- MP4/HLS capture',
        domains=['motionarray.com', 'www.motionarray.com'],
        start_url='https://motionarray.com/stock-video/',
        license_name='Motion Array license terms',
        license_url='https://motionarray.com/license/terms/',
        attribution_required='Per subscription license',
        terms_url='https://motionarray.com/license/terms/',
        preview_status='Preview',
        catalog_patterns=['/stock-video', '/video-templates', '/motion-graphics'],
        item_patterns=['/stock-video/', '/video-templates/', '/motion-graphics/'],
        exclude_patterns=[
            '/browse/', '/pricing', '/learn', '/plugins', '/music', '/sound-effects',
            '/photos', '/login', '/account',
        ],
        item_url_regex=r'motionarray\.com/(?:stock-video|video-templates|motion-graphics)/[^/?#]+-\d+(?:[/?#]|$)',
        clip_id_regex=r'motionarray\.com/(?:stock-video|video-templates|motion-graphics)/[^/?#]+-(\d+)(?:[/?#]|$)',
        video_types=['mp4', 'webm', 'm3u8', 'mpd'],
        scroll_items=True,
        og_fallback=True,
        jsonld_fallback=True,
        catalog_card_js="""
        (() => {
            const clips = [];
            const seen = new Set();
            const clean = (s) => (s || '').replace(/\\s+/g, ' ').trim();
            const idFromHref = (href) => {
                const m = (href || '').match(/\\/(?:stock-video|video-templates|motion-graphics)\\/[^/?#]+-(\\d+)(?:[/?#]|$)/i);
                return m ? m[1] : '';
            };
            const bestImage = (root) => {
                const media = root.querySelector('video[poster], img[src], img[data-src], img[srcset]');
                if (!media) return '';
                if (media.poster) return media.poster;
                if (media.src) return media.src;
                if (media.dataset && media.dataset.src) return media.dataset.src;
                if (media.srcset) {
                    const parts = media.srcset.split(',').map(s => s.trim().split(' ')[0]).filter(Boolean);
                    return parts[parts.length - 1] || '';
                }
                return '';
            };
            document.querySelectorAll('a[href]').forEach(a => {
                const href = a.href || a.getAttribute('href') || '';
                const id = idFromHref(href);
                if (!id || seen.has(id)) return;
                const root = a.closest('article, li, [data-testid], [class*="product"], [class*="card"], [class*="tile"]') || a;
                const text = clean(root.innerText);
                const thumb = bestImage(root);
                if (!thumb && !text) return;
                seen.add(id);
                const title =
                    clean(a.getAttribute('aria-label') || a.getAttribute('title')) ||
                    clean((root.querySelector('h1,h2,h3,[class*="title"]') || {}).innerText) ||
                    clean((root.querySelector('img[alt]') || {}).alt);
                const duration = (text.match(/\\b\\d{1,2}:\\d{2}(?::\\d{2})?\\b/) || [''])[0];
                clips.push({
                    clip_id: id,
                    title,
                    creator: clean((root.querySelector('[class*="author"], [class*="creator"]') || {}).innerText),
                    duration,
                    thumbnail_url: thumb,
                    source_url: href.startsWith('http') ? href : location.origin + href,
                    resolution: '',
                    tags: '',
                    collection: '',
                    m3u8_url: '',
                    frame_rate: '',
                    camera: '',
                    formats: 'Preview',
                });
            });
            return clips;
        })()
        """,
    )
