import subprocess, json

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0'

raw = subprocess.run(['curl','-s','-m','25','-A',UA,
                      'https://atsu.moe/api/read/chapter?mangaId=cmgzlqc5aeuq3m191ynp3h67w&chapterId=PwTgD1Gh'],
                     capture_output=True, text=True).stdout
path = json.loads(raw)['readChapter']['pages'][0]['image']
print('raw path:', path)

for u in ['https://cdn.atsu.moe' + path,
          'https://atsu.moe' + path,
          'https://cdn.atsu.moe/static/' + path.lstrip('/'),
          'https://cdn.atsu.moe/' + path.lstrip('/').replace('static/', '')]:
    c = subprocess.run(['curl','-s','-o','/dev/null','-m','25',
                        '-w','%{http_code}|%{content_type}|%{size_download}',
                        '-A',UA,'-H','Referer: https://atsu.moe/', u],
                       capture_output=True, text=True).stdout
    print(f'  {c:26s} {u}')
