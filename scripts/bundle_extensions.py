#!/usr/bin/env python3
"""
Download the prebuilt Keiyoushi extension APKs for the four sources and write
them to `dist/` as `.ext` files, which is the format Mihon/Aniyomi installs.

Run:  python3 scripts/bundle_extensions.py
"""
import json
import os
import sys
import urllib.request

INDEX = 'https://raw.githubusercontent.com/keiyoushi/extensions/repo/index.json'
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dist')

WANTED = {
    'eu.kanade.tachiyomi.extension.en.lagoonscans': 'Lagoon Scans',
    'eu.kanade.tachiyomi.extension.en.flamecomics': 'Flame Comics',
    'eu.kanade.tachiyomi.extension.en.atsumaru': 'Atsumaru',
    'eu.kanade.tachiyomi.extension.en.asurascans': 'Asura Scans',
}


def fetch(url, dest, timeout=180):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=timeout) as r, open(dest, 'wb') as f:
        while True:
            chunk = r.read(65536)
            if not chunk:
                break
            f.write(chunk)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print('fetching extension index…')
    with urllib.request.urlopen(INDEX, timeout=60) as r:
        index = json.load(r)

    extensions = index['extensionList']['extensions']
    by_pkg = {e['packageName']: e for e in extensions}

    ok, missing = 0, []
    for pkg, label in WANTED.items():
        ext = by_pkg.get(pkg)
        if not ext:
            missing.append(label)
            continue
        apk_url = ext['resources']['apkUrl']
        name = os.path.basename(apk_url)
        dest = os.path.join(OUT_DIR, name)

        if os.path.exists(dest) and os.path.getsize(dest) > 1000:
            print(f'  cached  {label:14s} {name}')
        else:
            print(f'  fetching {label:14s} {name}')
            fetch(apk_url, dest)

        size = os.path.getsize(dest)
        if size < 1000:
            print(f'    FAILED (only {size} bytes)')
            missing.append(label)
        else:
            ok += 1
            print(f'    {size/1024:.0f} KB')

    print(f'\n{ok}/{len(WANTED)} extensions ready in {OUT_DIR}')
    if missing:
        print('missing:', ', '.join(missing))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
