import subprocess, json

def pages(src, slug, ch):
    r = subprocess.run(['python3', 'scripts/scrape.py', '--source', src,
                        '--slug', slug, '--chapter', str(ch)],
                       capture_output=True, text=True, cwd='/home/hermes/manhwa-extensions')
    return json.loads(r.stdout)

checks = [
    ('flame', '1', 200),
    ('atsu', 'oZOG5', 200),
    ('lagoon', 'absolute-sword-sense', 209),
]

for src, slug, ch in checks:
    d = pages(src, slug, ch)
    u = d['pages'][0]
    c = subprocess.run(['curl', '-s', '-o', '/dev/null', '-m', '25',
                        '-w', '%{http_code}|%{content_type}|%{size_download}',
                        '-A', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0',
                        '-H', f'Referer: https://{"flamecomics.xyz" if src=="flame" else ("atsu.moe" if src=="atsu" else "lagoonscans.com")}/',
                        u], capture_output=True, text=True).stdout
    print(f'{src:8s} ch{ch}: {d["page_count"]:3d} pages | {c} | {u[:90]}')
