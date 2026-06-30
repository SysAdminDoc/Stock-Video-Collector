"""Built-in Adobe Stock site profile and contract fixtures."""

PROFILE_NAME = 'Adobe Stock'
CONTRACT = {'catalog_urls': ['https://stock.adobe.com/video', 'https://stock.adobe.com/search/video?k=office'],
 'item_urls': [{'url': 'https://stock.adobe.com/video/sample-stock-clip/123456789',
                'clip_id': '123456789'}],
 'excluded_urls': ['https://stock.adobe.com/photos/sample/123456789'],
 'video_urls': [{'url': 'https://stock.adobe.com/previews/sample.mp4', 'allowed': True}]}


def build(SiteProfile):
    """Return a configured SiteProfile instance."""
    return SiteProfile(
        'Adobe Stock',
        description='Adobe Stock Video public watermarked previews -- MP4/HLS capture',
        domains=['stock.adobe.com', 'www.stock.adobe.com'],
        start_url='https://stock.adobe.com/video',
        license_name='Adobe Stock license terms',
        license_url='https://stock.adobe.com/license-terms',
        attribution_required='Per license',
        terms_url='https://stock.adobe.com/license-terms',
        preview_status='Watermarked preview',
        catalog_patterns=['/video', '/search/video', '/collections/', '/free/'],
        item_patterns=['/video/'],
        exclude_patterns=[
            '/images/', '/photos/', '/illustrations/', '/vectors/', '/templates/',
            '/3d-assets/', '/audio/', '/fonts/', '/plugins/', '/plans',
            '/enterprise', '/contributor', '/help', '/legal', '/profile',
        ],
        item_url_regex=(
            r'stock\.adobe\.com/(?:[a-z]{2}/)?video/[^?#]+/\d{4,}(?:[?#]|$)|'
            r'[?&]asset_id=\d{4,}'
        ),
        clip_id_regex=r'(?:/video/[^?#]+/|[?&]asset_id=)(\d{4,})',
        video_types=['mp4', 'webm', 'm3u8', 'mpd'],
        scroll_items=True,
        og_fallback=True,
        jsonld_fallback=True,
        catalog_card_js="""
        (() => {
            const clips = [];
            const seen = new Set();
            const idFromHref = (href) => {
                if (!href) return '';
                const patterns = [
                    /stock\\.adobe\\.com\\/(?:[a-z]{2}\\/)?video\\/[^?#]+\\/(\\d{4,})(?:[?#]|$)/i,
                    /\\/video\\/[^?#]+\\/(\\d{4,})(?:[?#]|$)/i,
                    /[?&]asset_id=(\\d{4,})/i,
                    /[?&]content_id=(\\d{4,})/i
                ];
                for (const pat of patterns) {
                    const m = href.match(pat);
                    if (m) return m[1];
                }
                return '';
            };
            const cleanText = (s) => (s || '').replace(/\\s+/g, ' ').trim();
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
                const root = a.closest('article, li, [data-testid], [class*="asset"], [class*="card"], [class*="thumbnail"]') || a;
                const text = cleanText(root.innerText);
                const thumb = bestImage(root);
                if (!thumb && !text) return;
                seen.add(id);
                const title =
                    cleanText(a.getAttribute('aria-label') || a.getAttribute('title')) ||
                    cleanText((root.querySelector('h1,h2,h3,[class*="title"]') || {}).innerText) ||
                    cleanText((root.querySelector('img[alt]') || {}).alt);
                const durationMatch = text.match(/\\b\\d{1,2}:\\d{2}(?::\\d{2})?\\b/);
                const resolutionMatch = text.match(/\\b(?:4K|UHD|HD|\\d{3,5}\\s*[xX]\\s*\\d{3,5})\\b/);
                clips.push({
                    clip_id: id,
                    title,
                    creator: cleanText((root.querySelector('[class*="creator"], [class*="author"], [class*="contributor"]') || {}).innerText),
                    duration: durationMatch ? durationMatch[0] : '',
                    thumbnail_url: thumb,
                    source_url: href.startsWith('http') ? href : location.origin + href,
                    resolution: resolutionMatch ? resolutionMatch[0].replace(/\\s+/g, '') : '',
                    tags: '',
                    collection: '',
                    m3u8_url: '',
                    frame_rate: '',
                    camera: '',
                    formats: 'Watermarked preview',
                });
            });
            return clips;
        })()
        """,
    )
