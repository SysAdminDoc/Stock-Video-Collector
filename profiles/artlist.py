"""Built-in Artlist site profile and contract fixtures."""

PROFILE_NAME = 'Artlist'
CONTRACT = {'catalog_urls': ['https://artlist.io/stock-footage/'],
 'item_urls': [{'url': 'https://artlist.io/stock-footage/clip/sunset-harbor/123456',
                'clip_id': '123456'}],
 'excluded_urls': ['https://artlist.io/page/pricing'],
 'video_urls': [{'url': 'https://cdn.artlist.io/assets/clip/master.m3u8', 'allowed': True},
                {'url': 'https://cdn.artlist.io/assets/clip/preview.mp4', 'allowed': False}]}


def build(SiteProfile):
    """Return a configured SiteProfile instance."""
    return SiteProfile(
        'Artlist',
        description='Artlist.io stock footage — M3U8 HLS streams',
        domains=['artlist.io'],
        start_url='https://artlist.io/stock-footage/',
        license_name='Artlist license',
        license_url='https://artlist.io/license',
        attribution_required='Per subscription license',
        terms_url='https://artlist.io/license',
        preview_status='Licensed stream',
        catalog_patterns=['/stock-footage'],
        item_patterns=['/stock-footage/'],
        exclude_patterns=[
            '/sfx', '/stock-music', '/video-templates', '/song/',
            '/sound-effects', '/templates', '/playlist', '/browse',
            '/editorial', '/enterprise', '/teams', '/voice-over',
            '/royalty-free-music', '/luts', '/tools', '/favorites',
            '/downloads', '/spotlight', '/page/pricing',
        ],
        item_url_regex=r'/stock-footage/.+/\d{4,}$',
        video_types=['m3u8'],
        scroll_items=True,
        metadata_selectors={
            'clip_id':    r'Clip\s+ID\s+(\d+)',
            'resolution': r'Resolution[\s\n]+([\d]{3,5}\s*[xX\u00d7]\s*[\d]{3,5})',
            'duration':   r'Length[\s\n]+([\d:]{4,8})',
            'frame_rate': r'Frame\s+Rate[\s\n]+(\d+)',
            'camera':     r'Camera[\s\n]+([^\n\r]{2,50}?)(?:\n|\r|Available)',
            'formats':    r'Available\s+Formats[\s\n]+((?:(?:HD|SD|4K|2K|ProRes|MP4|MOV|RAW)\s*)+)',
            'creator':    r'Clip by\s*\n?\s*([^\n\r]{2,50})',
            'collection': r'Part of\s*\n?\s*([^\n\r]{2,60})',
            'tags':       r'Tags\s*\n((?:.+\n?){1,25}?)(?:Related|Part of|Clip by|Similar|Explore|$)',
        },
        og_fallback=True,
        catalog_card_js="""
        (() => {
            const clips = [];
            const seen = new Set();

            // ── Strategy 1: __NEXT_DATA__ (Next.js server-side props) ──
            try {
                const nd = document.getElementById('__NEXT_DATA__');
                if (nd) {
                    const data = JSON.parse(nd.textContent);
                    const walk = (obj) => {
                        if (!obj || typeof obj !== 'object') return;
                        if (Array.isArray(obj)) { obj.forEach(walk); return; }
                        // Look for clip-like objects with numeric IDs
                        const id = String(obj.id || obj.clipId || obj.clip_id || '');
                        if (id && /^\\d{4,}$/.test(id) && !seen.has(id)) {
                            seen.add(id);
                            clips.push({
                                clip_id: id,
                                title: obj.title || obj.name || obj.clipTitle || '',
                                creator: obj.artistName || obj.artist?.name || obj.creatorName || obj.creator || '',
                                duration: obj.duration || obj.length || '',
                                thumbnail_url: obj.thumbnailUrl || obj.thumbnail || obj.imageUrl || obj.image?.url || obj.posterUrl || '',
                                resolution: obj.resolution || '',
                                tags: Array.isArray(obj.tags) ? obj.tags.map(t => typeof t === 'string' ? t : t.name || '').join(', ') : (obj.tags || ''),
                                collection: obj.collectionName || obj.collection?.name || obj.folderName || '',
                                source_url: obj.url || obj.pageUrl || (id ? '/stock-footage/clip/' + id : ''),
                                m3u8_url: obj.videoUrl || obj.hlsUrl || obj.m3u8Url || obj.previewUrl || '',
                                frame_rate: obj.fps || obj.frameRate || '',
                                camera: obj.camera || obj.cameraModel || '',
                                formats: obj.formats || '',
                            });
                        }
                        Object.values(obj).forEach(walk);
                    };
                    walk(data);
                }
            } catch(e) {}

            // ── Strategy 2: DOM card parsing ──
            // Artlist cards: <a href="/stock-footage/..."> wrapping img + text
            try {
                const cards = document.querySelectorAll('a[href*="/stock-footage/"][href$="/"]' +
                    ', a[href*="/stock-footage/"][href*="/"]');
                cards.forEach(card => {
                    const href = card.href || card.getAttribute('href') || '';
                    const idM = href.match(/\\/(\\d{4,})\\/?$/);
                    if (!idM) return;
                    const id = idM[1];
                    if (seen.has(id)) return;
                    seen.add(id);

                    // Find thumbnail
                    const img = card.querySelector('img[src], img[data-src], img[srcset]');
                    let thumb = '';
                    if (img) {
                        thumb = img.src || img.dataset.src || '';
                        if (!thumb && img.srcset) {
                            const parts = img.srcset.split(',').map(s => s.trim().split(' ')[0]);
                            thumb = parts[parts.length - 1] || '';
                        }
                    }
                    // Also check picture > source
                    if (!thumb) {
                        const source = card.querySelector('picture source[srcset]');
                        if (source) {
                            const parts = source.srcset.split(',').map(s => s.trim().split(' ')[0]);
                            thumb = parts[parts.length - 1] || '';
                        }
                    }
                    // Background image fallback
                    if (!thumb) {
                        const bgEl = card.querySelector('[style*="background-image"]');
                        if (bgEl) {
                            const bgM = bgEl.style.backgroundImage.match(/url\\(['"]?([^'"\\)]+)/);
                            if (bgM) thumb = bgM[1];
                        }
                    }

                    // Find text content
                    const allText = card.innerText || '';
                    const lines = allText.split('\\n').map(l => l.trim()).filter(l => l);

                    // Duration: look for MM:SS or H:MM:SS pattern
                    let duration = '';
                    const durEl = card.querySelector('[class*="uration"], [class*="time"], [class*="length"]');
                    if (durEl) duration = durEl.innerText.trim();
                    if (!duration) {
                        for (const l of lines) {
                            if (/^\\d{1,2}:\\d{2}(:\\d{2})?$/.test(l)) { duration = l; break; }
                        }
                    }

                    // Title: first substantial text line that isn't duration
                    let title = '';
                    for (const l of lines) {
                        if (l === duration) continue;
                        if (l.length > 3 && l.length < 200 && !/^\\d{1,2}:\\d{2}/.test(l)) {
                            title = l; break;
                        }
                    }

                    // Creator: second text line or element with "by" prefix
                    let creator = '';
                    const byEl = card.querySelector('[class*="rtist"], [class*="reator"], [class*="author"]');
                    if (byEl) creator = byEl.innerText.trim().replace(/^by\\s+/i, '');

                    clips.push({
                        clip_id: id, title, creator, duration, thumbnail_url: thumb,
                        source_url: href.startsWith('http') ? href : location.origin + href,
                        resolution: '', tags: '', collection: '', m3u8_url: '',
                        frame_rate: '', camera: '', formats: '',
                    });
                });
            } catch(e) {}

            // ── Strategy 3: video elements with poster attributes ──
            try {
                document.querySelectorAll('video[poster]').forEach(v => {
                    const poster = v.poster || '';
                    const link = v.closest('a[href*="/stock-footage/"]');
                    if (!link) return;
                    const idM = link.href.match(/\\/(\\d{4,})\\/?$/);
                    if (!idM || seen.has(idM[1])) return;
                    seen.add(idM[1]);
                    clips.push({
                        clip_id: idM[1], title: '', creator: '', duration: '',
                        thumbnail_url: poster,
                        source_url: link.href.startsWith('http') ? link.href : location.origin + link.href,
                        resolution: '', tags: '', collection: '', m3u8_url: '',
                        frame_rate: '', camera: '', formats: '',
                    });
                });
            } catch(e) {}

            return clips;
        })()
        """,
    )
