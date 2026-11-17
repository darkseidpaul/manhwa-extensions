# Manhwa Extensions for Mihon / Aniyomi

Tachiyomi/Mihon extension modules for four manhwa sources.

| Source | Extension | Base URL | Status |
|---|---|---|---|
| Lagoon Scans | `LagoonScans` | https://lagoonscans.com | Verified — WP JSON, 5/5 chapters |
| Flame Comics | `FlameComics` | https://flamecomics.xyz | Verified — Next.js data API, 5/5 chapters |
| Atsumaru | `Atsumaru` | https://atsu.moe | Verified — JSON API, 5/5 chapters |
| Asura Scans | `AsuraScans` | https://asurascans.com | Upstream source |

Toraka (https://toraka.com) is **not** a hoster. It is an aggregator: its API
lists each series' real host in `available_sources`. Use it for discovery only.

## Prebuilt APKs

The Keiyoushi project already publishes these as official extensions.
Download from the releases below and install into Mihon/Aniyomi directly —
no build required:

| Source | APK |
|---|---|
| Flame Comics | `tachiyomi-en.flamecomics-v1.6.3.apk` |
| Atsumaru | `tachiyomi-en.atsumaru-v1.6.26.apk` |
| Lagoon Scans | `tachiyomi-en.lagoonscans-v1.6.2.apk` |
| Asura Scans | `tachiyomi-en.asurascans-v1.6.72.apk` |

Index: https://github.com/keiyoushi/extensions/repo/index.json
Releases: https://github.com/keiyoushi/extensions/releases

## Building from source

These modules target the Keiyoushi extension SDK (`libVersion = 1.6`) and are
built inside the `keiyoushi/extensions-source` monorepo. Copy each
`src/en/<name>/` directory into that repo and run:

```bash
./gradlew :src:en:flamecomics:assembleDebug
```

Output: `src/en/<name>/build/outputs/apk/debug/`

Requirements: JDK 17+, Android SDK (compileSdk 36). No Android Studio needed.

## Source notes (verified 2026-11-17)

### Lagoon Scans
WordPress. Easiest of the four.
- Series page: `https://lagoonscans.com/<slug>/`
- Chapter: `https://lagoonscans.com/<slug>-chapter-<n>/`
- REST: `https://lagoonscans.com/wp-json/wp/v2/posts?slug=<slug>-chapter-<n>`
  returns `content.rendered` with the `<img>` tags.
- Images: `https://iN.wp.com/lagoonscans.com/wp-content/uploads/YYYY/MM/NN-NNN.webp`
- No challenge on plain HTTP.

### Flame Comics
Next.js. Uses `/_next/data/<buildId>/...` JSON routes.
- Build id: read from `__NEXT_DATA__` in the homepage HTML (changes on deploy).
- Browse: `/_next/data/<buildId>/browse.json`
- Latest: `/_next/data/<buildId>/latest.json`
- Series: `/_next/data/<buildId>/series/<id>.json?id=<id>` → `pageProps.chapters`
- Chapter: `/_next/data/<buildId>/series/<id>/<token>.json?id=<id>&token=<token>`
  → `pageProps.chapter.images`
- Images: `https://cdn.flamecomics.xyz/uploads/images/series/<id>/<token>/<file>.jpg`
- Note: `flamescans.com` is a dead JS-gate domain and is NOT this site.

### Atsumaru
SPA, but the API is open and needs no token.
- Manga page: `https://atsu.moe/manga/<slug>` embeds a chapter list with
  `scanlationMangaId` (this is the `mangaId`) and chapter `id`.
- Details: `/api/manga/page?id=<slug>`
- Chapters: `/api/manga/allChapters?mangaId=<slug>`
- Reader: `/api/read/chapter?mangaId=<scanlationMangaId>&chapterId=<id>`
  → `readChapter.pages[].image`
- Images: `https://cdn.atsu.moe/static/pages/<slug>/<chapterId>/<n>.webp`
- One series aggregates several scanlation groups; each has its own
  `scanlationMangaId`, so pick the best-rated one per chapter.

### Toraka (discovery only)
- Search: `https://toraka.com/api/v1/search?q=<query>`
- Series: `https://toraka.com/api/v1/series/<slug>`
- Chapters: `https://toraka.com/api/v1/series/<slug>/chapters`
- Chapter pages are Cloudflare-gated and carry no page images.
