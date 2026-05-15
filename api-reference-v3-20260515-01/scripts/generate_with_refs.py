#!/usr/bin/env python3
"""Generate gpt-image-2 manga pages with multiple reference images.

Usage:
  set -a; source ~/.hermes/.env; set +a
  python3 scripts/generate_with_refs.py \
    --prompt prompts/01.txt \
    --out assets/01.png \
    --ref refs/character-sheet.png \
    --ref refs/style-sheet.png

Notes:
- Does not print API keys.
- Accepts multiple --ref entries; they are sent as image[].
- Expects OpenAI Images API to return b64_json.
"""
import argparse, base64, json, os, sys, urllib.request, urllib.error
from pathlib import Path
from uuid import uuid4


def multipart(fields, files):
    boundary = '----hermes-' + uuid4().hex
    body = bytearray()
    def add_line(s):
        body.extend(s.encode())
        body.extend(b'\r\n')
    for name, value in fields.items():
        add_line(f'--{boundary}')
        add_line(f'Content-Disposition: form-data; name="{name}"')
        add_line('')
        add_line(str(value))
    for field, path in files:
        path = Path(path)
        add_line(f'--{boundary}')
        add_line(f'Content-Disposition: form-data; name="{field}"; filename="{path.name}"')
        add_line('Content-Type: image/png')
        add_line('')
        body.extend(path.read_bytes())
        body.extend(b'\r\n')
    add_line(f'--{boundary}--')
    return bytes(body), boundary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--prompt', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--ref', action='append', default=[])
    ap.add_argument('--model', default='gpt-image-2')
    ap.add_argument('--size', default='1024x1536')
    ap.add_argument('--quality', default='medium')
    args = ap.parse_args()

    key = os.environ.get('OPENAI_API_KEY')
    if not key:
        raise SystemExit('OPENAI_API_KEY is not set')

    prompt = Path(args.prompt).read_text()
    refs = [Path(r) for r in args.ref]
    for r in refs:
        if not r.exists():
            raise SystemExit(f'reference not found: {r}')

    fields = {'model': args.model, 'prompt': prompt, 'size': args.size, 'quality': args.quality}
    files = [('image[]', r) for r in refs]
    body, boundary = multipart(fields, files)
    req = urllib.request.Request(
        'https://api.openai.com/v1/images/edits',
        data=body,
        headers={'Authorization': f'Bearer {key}', 'Content-Type': f'multipart/form-data; boundary={boundary}'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        msg = e.read().decode(errors='ignore')
        raise SystemExit(f'OpenAI API error {e.code}: {msg[:1000]}')

    if 'error' in data:
        raise SystemExit('OpenAI API error: ' + json.dumps(data['error'], ensure_ascii=False))
    item = data.get('data', [{}])[0]
    b64 = item.get('b64_json')
    if not b64:
        raise SystemExit('No b64_json in response: ' + json.dumps(data)[:1000])
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(base64.b64decode(b64))
    print(out.resolve())

if __name__ == '__main__':
    main()
