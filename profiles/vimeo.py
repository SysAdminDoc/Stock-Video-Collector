"""Built-in Vimeo site profile and contract fixtures."""

PROFILE_NAME = 'Vimeo'
CONTRACT = {'catalog_urls': ['https://vimeo.com/channels/freestockfootage'],
 'item_urls': [{'url': 'https://vimeo.com/channels/freestockfootage/123456789',
                'clip_id': '123456789'}],
 'excluded_urls': ['https://vimeo.com/pricing'],
 'video_urls': [{'url': 'https://vod-adaptive-ak.vimeocdn.com/sample/master.m3u8',
                 'allowed': True}]}


def build(SiteProfile):
    """Return a configured SiteProfile instance."""
    return SiteProfile(
        'Vimeo',
        description='Vimeo public stock/CC channels -- HLS and progressive MP4 previews',
        domains=['vimeo.com', 'www.vimeo.com', 'player.vimeo.com'],
        start_url='https://vimeo.com/channels/freestockfootage',
        license_name='Vimeo per-video license',
        license_url='https://vimeo.com/creativecommons',
        attribution_required='Per video license',
        terms_url='https://vimeo.com/terms',
        preview_status='Public preview',
        catalog_patterns=['/channels/', '/groups/', '/showcase/', '/album/', '/categories/'],
        item_patterns=['/video/', '/videos/'],
        exclude_patterns=[
            '/features', '/solutions', '/upgrade', '/pricing', '/enterprise',
            '/business', '/ott', '/livestream', '/blog', '/help', '/settings',
            '/manage/', '/upload', '/login', '/join',
        ],
        item_url_regex=(
            r'(?:vimeo\.com/(?:channels/[^/]+/|groups/[^/]+/videos/|'
            r'showcase/\d+/video/|album/\d+/video/)?\d{6,}|'
            r'player\.vimeo\.com/video/\d{6,})'
        ),
        video_types=['m3u8', 'mp4', 'webm', 'mpd'],
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
                    /vimeo\\.com\\/(?:channels\\/[^/]+\\/|groups\\/[^/]+\\/videos\\/|showcase\\/\\d+\\/video\\/|album\\/\\d+\\/video\\/)?(\\d{6,})(?:[/?#]|$)/i,
                    /player\\.vimeo\\.com\\/video\\/(\\d{6,})(?:[/?#]|$)/i,
                    /\\/(?:channels\\/[^/]+\\/|groups\\/[^/]+\\/videos\\/|showcase\\/\\d+\\/video\\/|album\\/\\d+\\/video\\/)?(\\d{6,})(?:[/?#]|$)/i
                ];
                for (const pat of patterns) {
                    const m = href.match(pat);
                    if (m) return m[1];
                }
                return '';
            };
            const bestImage = (root) => {
                const img = root.querySelector('img[src], img[data-src], img[srcset], video[poster]');
                if (!img) return '';
                if (img.poster) return img.poster;
                if (img.src) return img.src;
                if (img.dataset && img.dataset.src) return img.dataset.src;
                if (img.srcset) {
                    const parts = img.srcset.split(',').map(s => s.trim().split(' ')[0]).filter(Boolean);
                    return parts[parts.length - 1] || '';
                }
                return '';
            };
            document.querySelectorAll('a[href]').forEach(a => {
                const href = a.href || a.getAttribute('href') || '';
                const id = idFromHref(href);
                if (!id || seen.has(id)) return;
                const root = a.closest('article, li, [data-testid], [class*="clip"], [class*="video"], [class*="card"]') || a;
                const thumb = bestImage(root);
                if (!thumb && !(root.innerText || '').trim()) return;
                seen.add(id);
                const title =
                    (a.getAttribute('aria-label') || a.getAttribute('title') || '').trim() ||
                    ((root.querySelector('h1,h2,h3,[class*="title"]') || {}).innerText || '').trim() ||
                    ((root.querySelector('img[alt]') || {}).alt || '').trim();
                const creator =
                    ((root.querySelector('[class*="owner"], [class*="author"], [class*="user"], [class*="byline"]') || {}).innerText || '')
                        .replace(/^by\\s+/i, '').trim();
                const duration =
                    ((root.querySelector('time, [class*="duration"], [class*="time"]') || {}).innerText || '')
                        .trim();
                clips.push({
                    clip_id: id,
                    title,
                    creator,
                    duration,
                    thumbnail_url: thumb,
                    source_url: href.startsWith('http') ? href : location.origin + href,
                    resolution: '',
                    tags: '',
                    collection: '',
                    m3u8_url: '',
                    frame_rate: '',
                    camera: '',
                    formats: '',
                });
            });
            return clips;
        })()
        """,
    )
