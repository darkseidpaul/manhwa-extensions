import subprocess, json

print('=== repo metadata ===')
r = subprocess.run(['gh','api','repos/darkseidpaul/manhwa-extensions',
                    '--jq','"name=\(.full_name) public=\(.private|not) default=\(.default_branch) size=\(.size)KB pushed=\(.pushed_at)"'],
                   capture_output=True, text=True)
print(' ', r.stdout.strip() or r.stderr[:200])

print('\n=== top-level contents ===')
r = subprocess.run(['gh','api','repos/darkseidpaul/manhwa-extensions/contents','--jq','.[].name'],
                   capture_output=True, text=True)
print(' ', r.stdout.split())

print('\n=== extension modules present ===')
r = subprocess.run(['gh','api','repos/darkseidpaul/manhwa-extensions/contents/src/en','--jq','.[].name'],
                   capture_output=True, text=True)
print(' ', r.stdout.split())

print('\n=== APKs in dist/ ===')
r = subprocess.run(['gh','api','repos/darkseidpaul/manhwa-extensions/contents/dist','--jq','.[] | "\\(.name) \\(.size) bytes"'],
                   capture_output=True, text=True)
print(r.stdout.strip() or r.stderr[:200])

print('\n=== commit count ===')
r = subprocess.run(['gh','api','repos/darkseidpaul/manhwa-extensions/commits','--jq','length'],
                   capture_output=True, text=True)
print(' ', r.stdout.strip())
