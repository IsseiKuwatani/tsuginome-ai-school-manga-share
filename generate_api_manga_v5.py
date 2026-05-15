#!/usr/bin/env python3
"""Generate Tsuginome AI school manga LP via OpenAI Images API.
Direct API use is allowed only because the user explicitly requested API generation in this task.
"""
from __future__ import annotations
import base64, concurrent.futures, datetime as dt, json, os, sys, time, urllib.request, urllib.error, mimetypes, uuid
from pathlib import Path

REPO = Path(__file__).resolve().parent
RUN_ID = os.environ.get('RUN_ID') or dt.datetime.now().strftime('api-generated-%Y%m%d-%H%M')
OUT = REPO / RUN_ID
IMG_DIR = OUT / 'assets'
PROMPT_DIR = OUT / 'prompts'
MODEL = os.environ.get('OPENAI_IMAGE_MODEL', 'gpt-image-2')
SIZE = os.environ.get('OPENAI_IMAGE_SIZE', '1024x1536')
CONCURRENCY = int(os.environ.get('IMAGE_CONCURRENCY', '3'))
KEY = os.environ.get('OPENAI_API_KEY')
if not KEY:
    raise SystemExit('OPENAI_API_KEY is not loaded. Source ~/.hermes/.env before running.')
IMG_DIR.mkdir(parents=True, exist_ok=True)
PROMPT_DIR.mkdir(parents=True, exist_ok=True)

CHARACTER_BIBLE = """
Recurring characters. Keep them consistent on every page.
主人公: 佐伯ミナミ, 34歳女性フリーランス. Shoulder-length straight black hair, beige casual blazer, white inner shirt, slim build, laptop bag, adult realistic business-manga look. Expressions move from tired/anxious to skeptical to focused to hopeful. No childish mascot energy.
メンター: 桐谷さん, male in early 40s, Tsuginome practical AI operator. Navy jacket, white shirt, black rectangular glasses, short black hair, calm serious face, holds tablet or pen. Not flashy, not celebrity instructor.
Occasional cohort members: adult freelancers only, subtle background, not sidekicks.
Visual style: Japanese vertical webtoon / Piccoma-like adult business manga, real panel divisions, generous white gutters, speech bubbles, closeups, laptop/smartphone cutaways, modern Osaka business coworking mood but no tourist symbols, no takoyaki, no Osaka Castle, no Tsutenkaku, no Hanshin colors, no mascot.
Important: Japanese text must be large, clean, readable, and baked into the image. Use only the exact short Japanese copy specified for each page. Do not add extra unreadable pseudo text.
""".strip()

GLOBAL_STORY = """
A manga landing page for Tsuginome AI practical school. Target: working freelancers in Osaka/Kansai who already use ChatGPT or Gemini but are not yet using Claude Code / Codex to create deliverables. Core message: Claude Code and Codex are not optional anymore; freelancers without urgency about them are not the target. But do not overhype. Show skepticism, fear, online consultation, practical explanation, actual working tools, curriculum, price, caveats, selective trial opportunity, and final LINE CTA. CTA is LINE registration for a free bonus: AI実務化スターターキット.
""".strip()

PAGES = [
{
 'n':1,'title':'Hero / 焦り','copy':['AIを使っている。','なのに、仕事になっていない。','ChatGPTもGeminiも使ってる。','でも、納品できる形にできない。','LINEで無料資料を受け取る'],
 'prompt':'Full-page vertical manga LP hero. 3 panels: top close-up of Minami tired at laptop late night, middle black emotional caption, bottom CTA card. Strong hook but adult business tone. Large whitespace. No page number.'},
{
 'n':2,'title':'SNSで流れてくる危機感','copy':['Claude Codeで制作が変わる','Codexで実装スピードが変わる','名前は知ってる。','でも、正直こわい。','エンジニアじゃない私に関係あるの？'],
 'prompt':'Vertical manga with smartphone feed panel, anxious face close-up, wide silent panel with empty desk. Piccoma-like pacing, varied panels.'},
{
 'n':3,'title':'便利なAI止まり','copy':['文章は作れる。','投稿案も出せる。','リサーチも早い。','でも…','クライアントに出す形で止まる。'],
 'prompt':'Manga page showing Minami comparing AI text output and a client deliverable. Use 4 panels: laptop screen, hands stop typing, close-up eyes, document with red question marks. Keep text sparse.'},
{
 'n':4,'title':'AI副業スクール不信','copy':['誰でも簡単！','AI副業で月収◯◯万円！','こういうのは無理。','失敗したくない。','簡単には信じられない。'],
 'prompt':'Manga page with exaggerated smartphone ad in first panel, Minami skeptical turning phone face down, quiet white-space panel. Adult skeptical tone, not comedic.'},
{
 'n':5,'title':'LINE無料資料','copy':['でも、無料資料だけなら。','AI実務化スターターキット','Claude Code / Codex 最初の一歩','AIを納品物に変えるロードマップ','提出前チェックリスト'],
 'prompt':'Vertical manga + offer block page. Minami taps LINE on smartphone, then clean document kit cards appear. Manga panels around a clear LINE bonus block. No internal wording.'},
{
 'n':6,'title':'資料を読んで気づく','copy':['難しそうだから後で。','そう思って避けてた。','でも、触らない方が危ないのかも。','最初のハードルを越えたい。'],
 'prompt':'Quiet reading scene. 4 panels with document pages, Minami taking notes, close-up of her expression changing from worry to resolve. Plenty of white gutters.'},
{
 'n':7,'title':'オンライン個別相談へ','copy':['無料相談があるなら、','一回だけ聞いてみよう。','オンライン個別相談','いきなりオフラインじゃないなら安心。'],
 'prompt':'Manga page showing booking an online consultation and laptop video call screen. Avoid offline event. Modern home desk, natural laptop placement, no complex fingers.'},
{
 'n':8,'title':'メンター登場','copy':['Claude CodeやCodexは、','エンジニアだけのものではありません。','作れる範囲を広げる武器です。','でも、コードは書けません。'],
 'prompt':'Online consultation manga: mentor on laptop screen, Minami listening skeptically. Use split-screen panel, speech bubbles. Serious practical tone.'},
{
 'n':9,'title':'作るAIへ変わっている','copy':['もう、文章を出すAIだけじゃない。','LP、診断フォーム、業務ツール。','実際に動くものまで作れます。','たたき台で終わらせない。'],
 'prompt':'Visually exciting page: mentor explains, panels show a simple diagnostic web form running on laptop, an LP preview, a small dashboard. Emphasize actual working tools, not drafts.'},
{
 'n':10,'title':'非エンジニアの壁','copy':['最初はみんな怖いです。','でも一度触ると、','次々アイデアが出てきます。','今の仕事の延長で使える。'],
 'prompt':'Manga page with mentor calm, Minami imagining use cases around her: sales deck, LP improvement, diagnostic tool, automation. Dynamic but readable.'},
{
 'n':11,'title':'実務の流れ','copy':['AIに作らせる','人が確認する','直す','クライアントに出す','この流れを身につける。'],
 'prompt':'Process manga with 5 visually distinct panels, arrows embedded as manga motion. Minami checks output, revises, sends to client. Adult business manga.'},
{
 'n':12,'title':'4週間カリキュラム','copy':['4週間で触れる側へ','Week1 最初の壁を越える','Week2 提案・資料・LP改善','Week3 動くミニツール制作','Week4 レビューと納品品質'],
 'prompt':'Clean curriculum offer page but manga-styled, with Minami and mentor beside roadmap cards. Not too much text; large readable Japanese.'},
{
 'n':13,'title':'大阪オフラインは後半','copy':['まずはオンラインで安心して参加。','後半は大阪でレビュー。','実務に近い距離で、','成果物を磨く。'],
 'prompt':'Show transition from online learning to later Osaka coworking review. Modern business coworking only, subtle city energy, no tourist landmarks.'},
{
 'n':14,'title':'作れる成果物','copy':['作れるもの','LP改善案','診断ツール','営業資料','提案ワークフロー','ポートフォリオ事例'],
 'prompt':'Visual peak page showing polished outputs on screens and paper. Strong composition, panels of deliverables. No fake illegible UI except the specified labels.'},
{
 'n':15,'title':'価格前の不安','copy':['でも、料金は…？','高すぎたら無理。','安すぎても不安。','ちゃんと判断したい。'],
 'prompt':'Manga page focused on price anxiety. Minami looking at notes and calculator, quiet panels, skeptical expression. No offer hype.'},
{
 'n':16,'title':'0期価格と理由','copy':['0期価格 49,800円（税込）','講座改善への協力前提','成果物レビュー込み','納得してからで大丈夫です。'],
 'prompt':'Offer explanation page with mentor calmly explaining on video call / clean card. Transparent price and reason, not flashy sale design.'},
{
 'n':17,'title':'向いている人','copy':['向いている人','ChatGPTやGeminiは使っている','Claude Code / Codexに壁がある','提案できる範囲を広げたい','置いていかれる危機感がある'],
 'prompt':'Manga + checklist page. Minami checks boxes. Background freelancers working quietly. Adult design, readable checklist.'},
{
 'n':18,'title':'向いていない人','copy':['向いていない人','誰でも簡単に稼ぎたい人','危機感がない人','案件保証だけを期待する人','本気で触る気がない人'],
 'prompt':'Grounded caveat page, mentor serious. Use strong but not aggressive tone. No scammy vibes. Clear checklist block.'},
{
 'n':19,'title':'案件トライアルの現実','copy':['案件につながる可能性はあります。','でも、保証ではありません。','見るのは、成果物の品質。','納期、修正対応、連絡の安定性。'],
 'prompt':'Manga page about realistic job trial. Mentor explains caveat; panels show quality checklist, deadline calendar, communication chat. Honest tone.'},
{
 'n':20,'title':'決意と最終CTA','copy':['もう避けない。','まずは触ってみる。','Claude Code / Codex時代に','置いていかれないために。','AI実務化スターターキット','LINEで無料資料を受け取る'],
 'prompt':'Final strong vertical manga CTA. Morning light, Minami focused at laptop with hopeful expression, clean LINE bonus card and CTA. Emotional closure.'},
]

def api_json(url: str, payload: dict, timeout=180):
    data=json.dumps(payload).encode('utf-8')
    req=urllib.request.Request(url, data=data, method='POST', headers={
        'Authorization': f'Bearer {KEY}', 'Content-Type':'application/json'
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode('utf-8'))

def decode_image_response(resp: dict, path: Path):
    item=resp.get('data',[{}])[0]
    if item.get('b64_json'):
        path.write_bytes(base64.b64decode(item['b64_json']))
    elif item.get('url'):
        with urllib.request.urlopen(item['url'], timeout=120) as r:
            path.write_bytes(r.read())
    else:
        raise RuntimeError('No image data in API response: '+json.dumps(resp)[:500])
    if path.stat().st_size < 1000:
        raise RuntimeError(f'Image file too small: {path}')

def gen_image(prompt: str, out_path: Path, retries=2):
    payload={'model':MODEL,'prompt':prompt,'size':SIZE,'n':1}
    # Some models accept quality; if rejected, retry without it.
    if os.environ.get('OPENAI_IMAGE_QUALITY'):
        payload['quality']=os.environ['OPENAI_IMAGE_QUALITY']
    for attempt in range(retries+1):
        try:
            resp=api_json('https://api.openai.com/v1/images/generations', payload, timeout=240)
            decode_image_response(resp,out_path)
            return 'generation'
        except urllib.error.HTTPError as e:
            msg=e.read().decode('utf-8','ignore')[:1200]
            if 'quality' in payload and attempt == 0:
                payload.pop('quality',None)
                continue
            if attempt>=retries: raise RuntimeError(f'HTTP {e.code}: {msg}')
            time.sleep(4*(attempt+1))
        except Exception:
            if attempt>=retries: raise
            time.sleep(4*(attempt+1))

def multipart_edit(prompt: str, ref_path: Path, out_path: Path, retries=1):
    boundary='----HermesBoundary'+uuid.uuid4().hex
    fields=[('model',MODEL),('prompt',prompt),('size',SIZE),('n','1')]
    body=bytearray()
    def add_field(name,val):
        body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{val}\r\n'.encode())
    def add_file(name,path):
        ctype=mimetypes.guess_type(str(path))[0] or 'image/png'
        body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; filename="{path.name}"\r\nContent-Type: {ctype}\r\n\r\n'.encode())
        body.extend(path.read_bytes())
        body.extend(b'\r\n')
    for k,v in fields: add_field(k,v)
    # Try image field; OpenAI accepts image as file for edits.
    add_file('image', ref_path)
    body.extend(f'--{boundary}--\r\n'.encode())
    req=urllib.request.Request('https://api.openai.com/v1/images/edits', data=bytes(body), method='POST', headers={
        'Authorization': f'Bearer {KEY}', 'Content-Type': f'multipart/form-data; boundary={boundary}'
    })
    for attempt in range(retries+1):
        try:
            with urllib.request.urlopen(req, timeout=260) as r:
                resp=json.loads(r.read().decode('utf-8'))
            decode_image_response(resp,out_path)
            return 'edit'
        except Exception:
            if attempt>=retries: raise
            time.sleep(5*(attempt+1))

def prompt_for_page(p):
    copy=' / '.join(p['copy'])
    return f"""Create one finished portrait manga LP image, 1024x1536.
Use the reference character sheet if provided, and preserve character identity.

GLOBAL STORY:
{GLOBAL_STORY}

CHARACTER BIBLE:
{CHARACTER_BIBLE}

CURRENT PAGE {p['n']:02d}: {p['title']}
Page role: {p['prompt']}
Exact Japanese text to include, large and legible only:
{copy}

Manga layout requirements:
- Real vertical manga/webtoon page, not a flat poster.
- Use 3 to 6 panels with clear gutters, speech bubbles, closeups, device cutaways, and emotional pacing.
- Baked-in Japanese text only; do not add page numbers, section labels, lorem ipsum, fake gibberish, watermarks, or extra logos.
- Adult Japanese business manga style, clean line art, soft screen tones, modern UI, high readability on smartphone.
- Keep protagonist Minami and mentor visually consistent with the character sheet and bible.
""".strip()

def generate_character_sheet():
    path=IMG_DIR/'00-character-sheet.png'
    prompt=f"""Create a character reference sheet for a Japanese adult business manga LP.
{CHARACTER_BIBLE}
Show 2 main recurring characters with front view, half body, 3 expressions each, consistent outfit and colors.
Labels in Japanese: 佐伯ミナミ / 桐谷さん.
Clean white background, character sheet, no story panels, no page number. Large readable Japanese labels only.
""".strip()
    (PROMPT_DIR/'00-character-sheet.txt').write_text(prompt)
    if not path.exists() or path.stat().st_size < 1000:
        print('[character] generating', flush=True)
        gen_image(prompt,path)
    else:
        print('[character] exists, skipping', flush=True)
    return path

def generate_page(p, ref_path):
    n=p['n']; out=IMG_DIR/f'{n:02d}.png'; prompt=prompt_for_page(p)
    (PROMPT_DIR/f'{n:02d}.txt').write_text(prompt)
    if out.exists() and out.stat().st_size>1000:
        return (n,'skip',str(out))
    # Include adjacent context in prompt by mentioning neighbors.
    prev_title=PAGES[n-2]['title'] if n>1 else 'start'
    next_title=PAGES[n]['title'] if n<len(PAGES) else 'final CTA end'
    prompt += f"\n\nAdjacent context: previous page = {prev_title}; next page = {next_title}. Generate only current page {n:02d}."
    try:
        mode=multipart_edit(prompt,ref_path,out,retries=0)
    except Exception as e:
        (OUT/'edit_fallback.log').open('a').write(f'page {n:02d} edit failed: {repr(e)}\n')
        mode=gen_image(prompt,out,retries=2)
    return (n,mode,str(out))

def build_html():
    imgs='\n'.join([f'<img class="page" src="assets/{i:02d}.png" alt="ツギノメAI実務スクール漫画LP {i:02d}">' for i in range(1,len(PAGES)+1)])
    html=f'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ツギノメAI実務スクール 漫画LP API生成版</title>
<meta name="description" content="Claude Code / Codex時代に置いていかれないためのツギノメAI実務スクール漫画LP。">
<style>*{{box-sizing:border-box}}body{{margin:0;background:#111827;font-family:-apple-system,BlinkMacSystemFont,"Hiragino Sans","Yu Gothic",Meiryo,sans-serif}}.wrap{{max-width:520px;margin:0 auto;background:#fff;box-shadow:0 0 60px #0009}}.page{{display:block;width:100%;height:auto;margin:0;border:0}}.cta{{position:fixed;left:50%;bottom:12px;transform:translateX(-50%);z-index:20;width:min(480px,calc(100% - 24px));display:block;text-align:center;text-decoration:none;background:#06c755;color:#fff;border:3px solid #111;border-radius:999px;padding:14px 16px;font-weight:900;box-shadow:0 5px 0 #000}}.note{{max-width:520px;margin:0 auto;background:#fff;padding:18px 16px 96px;color:#444;font-size:12px;line-height:1.8}}.note a{{font-weight:800;color:#2563eb}}@media(min-width:760px){{.cta{{display:none}}}}</style>
</head><body><main class="wrap">{imgs}</main><a class="cta" href="#line-url-pending">LINEで無料資料を受け取る</a><div class="note" id="line-url-pending"><b>API生成版</b><br>公式LINE URLが決まり次第、このCTAを差し替えます。過去版を残すため、この生成物は専用URL <code>{RUN_ID}/</code> に保存しています。<br><a href="prompts/00-character-sheet.txt">character prompt</a></div></body></html>'''
    (OUT/'index.html').write_text(html)

if __name__=='__main__':
    print('RUN_ID=',RUN_ID)
    print('OUT=',OUT)
    print('MODEL=',MODEL,'SIZE=',SIZE,'CONCURRENCY=',CONCURRENCY)
    ref=generate_character_sheet()
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        futs=[ex.submit(generate_page,p,ref) for p in PAGES]
        for fut in concurrent.futures.as_completed(futs):
            res=fut.result()
            results.append(res)
            print('[page]',res,flush=True)
    build_html()
    print('DONE',OUT)
