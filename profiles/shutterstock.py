"""Built-in Shutterstock site profile and contract fixtures."""

PROFILE_NAME = 'Shutterstock'
CONTRACT = {'catalog_urls': ['https://www.shutterstock.com/video'],
 'item_urls': [{'url': 'https://www.shutterstock.com/video/clip-1105380147-aerial-city',
                'clip_id': '1105380147'}],
 'excluded_urls': ['https://www.shutterstock.com/photos'],
 'video_urls': [{'url': 'https://ak.picdn.net/shutterstock/videos/clip.mp4', 'allowed': True}]}


def build(SiteProfile):
    """Return a configured SiteProfile instance."""
    return SiteProfile(
        'Shutterstock',
        description='Shutterstock Video public previews -- MP4/HLS capture',
        domains=['shutterstock.com', 'www.shutterstock.com'],
        start_url='https://www.shutterstock.com/video',
        license_name='Shutterstock license',
        license_url='https://www.shutterstock.com/license',
        attribution_required='Per license',
        terms_url='https://www.shutterstock.com/license',
        preview_status='Preview',
        catalog_patterns=['/video', '/video/search', '/search/'],
        item_patterns=['/video/clip-'],
        exclude_patterns=[
            '/image-', '/photos', '/vectors', '/illustrations', '/music',
            '/editorial', '/pricing', '/business', '/contributors', '/login',
        ],
        item_url_regex=r'shutterstock\.com/video/clip-\d+[^?#]*(?:[?#]|$)',
        clip_id_regex=r'/video/clip-(\d+)',
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
                const m = (href || '').match(/\\/video\\/clip-(\\d+)[^?#]*(?:[?#]|$)/i);
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
            document.querySelectorAll('a[href*="/video/clip-"]').forEach(a => {
                const href = a.href || a.getAttribute('href') || '';
                const id = idFromHref(href);
                if (!id || seen.has(id)) return;
                const root = a.closest('article, li, [data-testid], [class*="asset"], [class*="card"], [class*="tile"]') || a;
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
                    creator: clean((root.querySelector('[class*="contributor"], [class*="author"], [class*="creator"]') || {}).innerText),
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
