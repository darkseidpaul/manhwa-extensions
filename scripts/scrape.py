#!/usr/bin/env python3
"""
Scrape manhwa chapters from Lagoon Scans, Flame Comics, and Atsumaru.

Each source is a thin adapter exposing the same three calls:
    popular(page) -> list of series dicts
    chapters(slug) -> list of chapter dicts
    pages(manga_id, chapter_id) -> list of image URLs

Nothing here is Tachiyomi-specific; the same functions back the Android
extensions in ../src/en/. Verified 2026-11-17.

Usage:
    python3 scrape.py --source lagoon --slug absolute-sword-sense --list
    python3 scrape.py --source lagoon --slug absolute-sword-sense --chapters
    python3 scrape.py --source lagoon --slug absolute-sword-sense --chapter 209
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/124.0 Safari/537.36')

# How many times to retry a request that came back empty or throttled.
TRIES = 4


def http_get(url, accept='application/json', referer=None):
    """GET with retries. Returns decoded text or raises."""
    last = None
    for attempt in range(TRIES):
        req = urllib.request.Request(url, headers={
            'User-Agent': UA,
            'Accept': accept,
            'Accept-Language': 'en-US,en;q=0.9',
        })
        if referer:
            req.add_header('Referer', referer)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode('utf-8', 'replace')
            if body.strip():
                return body
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 500, 502, 503):
                continue
            raise
        except Exception as e:
            last = e
    raise last or RuntimeError(f'no response from {url}')


def jget(url, **kw):
    return json.loads(http_get(url, **kw))


# --------------------------------------------------------------------------
# Lagoon Scans — WordPress
# --------------------------------------------------------------------------
class LagoonScans:
    name = 'lagoonscans'
    base = 'https://lagoonscans.com'

    def popular(self, page=1):
        """The homepage lists chapter posts; series slugs come from them."""
        html = http_get(f'{self.base}/page/{page}/', accept='text/html')
        slugs = set()
        for m in re.finditer(rf'{self.base}/([a-z0-9\-]+)-chapter-(\d+)/', html):
            slugs.add(m.group(1))
        return [{'slug': s, 'title': s.replace('-', ' ').title()} for s in sorted(slugs)]

    def chapters(self, slug):
        html = http_get(f'{self.base}/{slug}/', accept='text/html')
        found = re.findall(
            rf'{re.escape(self.base)}/({re.escape(slug)}-chapter-(\d+)/)', html)
        out, seen = [], set()
        for _slug_path, num in found:
            n = int(num)
            if n in seen:
                continue
            seen.add(n)
            out.append({'number': n, 'slug': f'{slug}-chapter-{n}',
                        'url': f'{self.base}/{slug}-chapter-{n}/'})
        return sorted(out, key=lambda c: c['number'])

    def pages(self, _slug, chapter_slug):
        """One WP REST call returns the chapter HTML with all images."""
        data = jget(f'{self.base}/wp-json/wp/v2/posts?slug={chapter_slug}'
                    '&_fields=id,slug,content')
        if not data:
            return []
        html = data[0].get('content', {}).get('rendered', '')
        urls = re.findall(r'(https://i\d\.wp\.com/[^"\']+\.(?:jpg|jpeg|png|webp))', html)
        # drop site icons / thumbnails
        return [u for u in urls if '/uploads/20' in u]


# --------------------------------------------------------------------------
# Flame Comics — Next.js data routes
# --------------------------------------------------------------------------
class FlameComics:
    name = 'flamecomics'
    base = 'https://flamecomics.xyz'
    cdn = 'https://cdn.flamecomics.xyz/uploads/images/series'

    def _build_id(self):
        html = http_get(self.base + '/', accept='text/html')
        m = re.search(r'"buildId":"([^"]+)"', html)
        if not m:
            raise RuntimeError('buildId not found — site layout changed')
        return m.group(1)

    def _data(self, path, **params):
        bid = self._build_id()
        qs = '&'.join(f'{k}={v}' for k, v in params.items())
        sep = '&' if qs else ''
        url = f'{self.base}/_next/data/{bid}/{path}?{qs}{sep}'
        return jget(url)['pageProps']

    def popular(self, page=1):
        props = self._data('browse.json')
        out = []
        for s in props.get('series', []):
            sid = s.get('series_id')
            if not sid:
                continue
            out.append({'slug': str(sid), 'title': s.get('title', ''),
                        'series_id': sid,
                        'cover': f'{self.cdn}/{sid}/{s.get("cover", "cover.png")}'})
        return out

    def chapters(self, series_id):
        props = self._data(f'series/{series_id}.json', id=series_id)
        out = []
        for c in props.get('chapters', []):
            token = c.get('token')
            if not token:
                continue
            num = float(c.get('chapter', 0))
            out.append({
                'number': num,
                'token': token,
                'series_id': c.get('series_id', series_id),
                'title': f"Chapter {num:g}" + (f" - {c['title']}" if c.get('title') else ''),
                'url': f'{self.base}/series/{series_id}/{token}',
            })
        return sorted(out, key=lambda c: c['number'])

    def pages(self, series_id, chapter_token):
        props = self._data(f'series/{series_id}/{chapter_token}.json',
                           id=series_id, token=chapter_token)
        chapter = props.get('chapter', {})
        sid = chapter.get('series_id', series_id)
        token = chapter.get('token', chapter_token)
        images = chapter.get('images') or {}
        # values are objects like {"name": "SL-200-0.jpg", "type": "image/jpeg", ...}
        names = [v['name'] if isinstance(v, dict) else v for v in images.values()]
        return [f'{self.cdn}/{sid}/{token}/{n}' for n in names]


# --------------------------------------------------------------------------
# Atsumaru — JSON API (no token required)
# --------------------------------------------------------------------------
class Atsumaru:
    name = 'atsumaru'
    base = 'https://atsu.moe'
    cdn = 'https://cdn.atsu.moe'

    def popular(self, page=1):
        offset = (page - 1) * 40
        data = jget(
            f'{self.base}/api/home2/popular?offset={offset}&limit=40'
            '&types=Manga,Manwha,Manhua,OEL&mediums=Comic&timeframe=daily')
        return [{'slug': it['id'], 'title': it.get('title', '')} for it in data.get('items', [])]

    def chapters(self, slug):
        data = jget(f'{self.base}/api/manga/allChapters?mangaId={slug}')
        out = []
        for c in data.get('chapters', []):
            out.append({
                'id': c['id'],
                'manga_id': c.get('scanlationMangaId') or slug,
                'number': float(c.get('number', 0)),
                'title': c.get('title') or '',
                'url': f'{self.base}/read/{slug}/{c["id"]}',
            })
        return sorted(out, key=lambda c: c['number'])

    def pages(self, manga_id, chapter_id):
        data = jget(f'{self.base}/api/read/chapter?mangaId={manga_id}&chapterId={chapter_id}')
        pages = data.get('readChapter', {}).get('pages', [])
        return [self._abs(p['image']) for p in pages]

    def _abs(self, path):
        if path.startswith('http'):
            return path
        if path.startswith('//'):
            return 'https:' + path
        # API returns "/static/pages/<slug>/<chapterId>/<n>.webp";
        # served from the CDN host, keeping the leading /static/.
        return f'{self.cdn}{path if path.startswith("/") else "/" + path}'


SOURCES = {
    'lagoon': LagoonScans,
    'lagoonscans': LagoonScans,
    'flame': FlameComics,
    'flamecomics': FlameComics,
    'atsu': Atsumaru,
    'atsumaru': Atsumaru,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', required=True, choices=sorted(SOURCES))
    ap.add_argument('--slug', help='series slug (or numeric id for Flame)')
    ap.add_argument('--list', action='store_true', help='list series')
    ap.add_argument('--chapters', action='store_true', help='list chapters')
    ap.add_argument('--chapter', help='fetch one chapter\'s pages')
    ap.add_argument('--limit', type=int, default=10)
    args = ap.parse_args()

    src = SOURCES[args.source]()

    if args.list:
        for s in src.popular()[:args.limit]:
            print(json.dumps(s, ensure_ascii=False))
        return

    if not args.slug:
        ap.error('--slug is required unless --list is used')

    if args.chapters:
        for c in src.chapters(args.slug)[:args.limit]:
            print(json.dumps(c, ensure_ascii=False))
        return

    if args.chapter:
        # search the FULL chapter list -- --limit only applies to --chapters
        ch = next((c for c in src.chapters(args.slug)
                   if str(int(c.get('number', 0))) == args.chapter.lstrip('0') or
                   str(c.get('number')) == args.chapter), None)
        if ch is None:
            sys.exit(f'chapter {args.chapter} not found')
        if src.name == 'flamecomics':
            pages = src.pages(ch['series_id'], ch['token'])
        else:
            pages = src.pages(ch.get('manga_id', args.slug), ch.get('id') or ch['slug'])
        print(json.dumps({'chapter': ch, 'page_count': len(pages), 'pages': pages},
                         ensure_ascii=False, indent=1))
        return

    ap.error('pick --list, --chapters, or --chapter')


if __name__ == '__main__':
    main()
