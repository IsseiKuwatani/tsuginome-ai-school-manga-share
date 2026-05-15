#!/usr/bin/env python3
import argparse, base64, json, os, urllib.request, urllib.error
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument('--prompt', required=True)
ap.add_argument('--out', required=True)
ap.add_argument('--model', default='gpt-image-2')
ap.add_argument('--size', default='1024x1536')
ap.add_argument('--quality', default='medium')
args=ap.parse_args()
key=os.environ.get('OPENAI_API_KEY')
if not key: raise SystemExit('OPENAI_API_KEY is not set')
prompt=Path(args.prompt).read_text()
payload={'model':args.model,'prompt':prompt,'size':args.size,'quality':args.quality}
body=json.dumps(payload).encode()
req=urllib.request.Request('https://api.openai.com/v1/images/generations',data=body,headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'},method='POST')
try:
    with urllib.request.urlopen(req,timeout=300) as resp:
        data=json.loads(resp.read().decode())
except urllib.error.HTTPError as e:
    raise SystemExit(f'OpenAI API error {e.code}: '+e.read().decode(errors='ignore')[:1000])
if 'error' in data: raise SystemExit('OpenAI API error: '+json.dumps(data['error'],ensure_ascii=False))
item=data.get('data',[{}])[0]
b64=item.get('b64_json')
if not b64: raise SystemExit('No b64_json: '+json.dumps(data)[:1000])
out=Path(args.out); out.parent.mkdir(parents=True,exist_ok=True); out.write_bytes(base64.b64decode(b64))
print(out.resolve())
