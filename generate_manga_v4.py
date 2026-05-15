from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import textwrap, math, os

BASE = Path(__file__).resolve().parent
OUT = BASE / 'assets' / 'manga-v4'
OUT.mkdir(parents=True, exist_ok=True)
W,H = 1080,1920
FONT_PATH = '/System/Library/AssetsV2/PreinstalledAssetsV2/InstallWithOs/com_apple_MobileAsset_Font7/11ead4dd9f3a3503b4ced2546782dd8bc31871c9.asset/AssetData/YuGothic-Medium.otf'
JP_PATH = '/System/Library/AssetsV2/PreinstalledAssetsV2/InstallWithOs/com_apple_MobileAsset_Font7/0703ece025f7511095fc290b30bc2d3d28d509a9.asset/AssetData/YuGothic-Bold.otf'

def font(size, bold=False):
    path = JP_PATH if bold and Path(JP_PATH).exists() else FONT_PATH
    if not Path(path).exists():
        path = '/System/Library/Fonts/Supplemental/AppleGothic.ttf'
    return ImageFont.truetype(path, size=size)

F = {
 'title': font(64, True), 'h': font(48, True), 'body': font(37), 'small': font(28),
 'tiny': font(22), 'bubble': font(35), 'black': font(42, True), 'cta': font(40, True)
}

def text_size(draw, text, f):
    b=draw.textbbox((0,0), text, font=f)
    return b[2]-b[0], b[3]-b[1]

def wrap_jp(draw, text, f, max_w):
    lines=[]
    for para in text.split('\n'):
        cur=''
        for ch in para:
            if ch == ' ':
                test=cur+ch
            else:
                test=cur+ch
            if text_size(draw, test, f)[0] <= max_w:
                cur=test
            else:
                if cur: lines.append(cur)
                cur=ch
        if cur: lines.append(cur)
    return lines

def draw_wrapped(draw, xy, text, f, fill=(25,25,25), max_w=700, line_h=None, align='left'):
    x,y=xy; line_h=line_h or int(f.size*1.35)
    for line in wrap_jp(draw,text,f,max_w):
        tw,_=text_size(draw,line,f)
        xx=x if align=='left' else x+(max_w-tw)//2
        draw.text((xx,y),line,font=f,fill=fill)
        y += line_h
    return y

def panel(draw, box, fill=(255,255,255), width=7, radius=0):
    x1,y1,x2,y2=box
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=(18,18,18), width=width)

# simplified recurring characters
def person(draw, cx, cy, scale=1.0, kind='hero', mood='normal'):
    s=scale
    # body
    jacket = (210,181,140) if kind=='hero' else (35,55,95)
    skin=(247,215,188); hair=(35,32,32)
    draw.ellipse((cx-60*s,cy-180*s,cx+60*s,cy-60*s), fill=skin, outline=(15,15,15), width=max(2,int(4*s)))
    if kind=='hero':
        draw.pieslice((cx-72*s,cy-202*s,cx+72*s,cy-78*s),180,360,fill=hair,outline=(15,15,15),width=max(2,int(3*s)))
        draw.rectangle((cx-70*s,cy-135*s,cx-48*s,cy-60*s), fill=hair)
        draw.rectangle((cx+48*s,cy-135*s,cx+70*s,cy-60*s), fill=hair)
    else:
        draw.arc((cx-65*s,cy-195*s,cx+65*s,cy-95*s),180,360,fill=hair,width=max(5,int(10*s)))
        # glasses
        draw.rectangle((cx-46*s,cy-125*s,cx-10*s,cy-98*s), outline=(0,0,0), width=max(2,int(3*s)))
        draw.rectangle((cx+10*s,cy-125*s,cx+46*s,cy-98*s), outline=(0,0,0), width=max(2,int(3*s)))
        draw.line((cx-10*s,cy-112*s,cx+10*s,cy-112*s), fill=(0,0,0), width=max(2,int(3*s)))
    # eyes/mouth
    if mood=='worried':
        draw.arc((cx-36*s,cy-122*s,cx-14*s,cy-108*s),180,360,fill=(0,0,0),width=max(2,int(3*s)))
        draw.arc((cx+14*s,cy-122*s,cx+36*s,cy-108*s),180,360,fill=(0,0,0),width=max(2,int(3*s)))
        draw.arc((cx-22*s,cy-86*s,cx+22*s,cy-64*s),180,360,fill=(0,0,0),width=max(2,int(3*s)))
    elif mood=='smile':
        draw.arc((cx-36*s,cy-126*s,cx-14*s,cy-104*s),0,180,fill=(0,0,0),width=max(2,int(3*s)))
        draw.arc((cx+14*s,cy-126*s,cx+36*s,cy-104*s),0,180,fill=(0,0,0),width=max(2,int(3*s)))
        draw.arc((cx-24*s,cy-94*s,cx+24*s,cy-60*s),0,180,fill=(0,0,0),width=max(2,int(3*s)))
    else:
        draw.line((cx-36*s,cy-112*s,cx-16*s,cy-112*s), fill=(0,0,0), width=max(2,int(3*s)))
        draw.line((cx+16*s,cy-112*s,cx+36*s,cy-112*s), fill=(0,0,0), width=max(2,int(3*s)))
        draw.line((cx-18*s,cy-75*s,cx+18*s,cy-75*s), fill=(0,0,0), width=max(2,int(3*s)))
    # torso
    draw.polygon([(cx-105*s,cy-55*s),(cx+105*s,cy-55*s),(cx+145*s,cy+155*s),(cx-145*s,cy+155*s)], fill=jacket, outline=(15,15,15))
    draw.polygon([(cx-45*s,cy-55*s),(cx+45*s,cy-55*s),(cx+20*s,cy+145*s),(cx-20*s,cy+145*s)], fill=(255,255,255), outline=(15,15,15))

def speech(draw, box, text, f=None, tail=None, fill=(255,255,255), stroke=(15,15,15), max_w=None, align='left'):
    f=f or F['bubble']; x1,y1,x2,y2=box
    draw.rounded_rectangle(box, radius=28, fill=fill, outline=stroke, width=5)
    if tail:
        tx,ty=tail
        # Short comic tail; do not draw a long pointer across the panel.
        if tx < x1:
            cy=max(y1+45,min(y2-45,ty)); pts=[(x1+6,cy-22),(x1+6,cy+22),(x1-46,cy)]
        elif tx > x2:
            cy=max(y1+45,min(y2-45,ty)); pts=[(x2-6,cy-22),(x2-6,cy+22),(x2+46,cy)]
        elif ty > y2:
            cx=max(x1+55,min(x2-55,tx)); pts=[(cx-24,y2-6),(cx+24,y2-6),(cx,y2+48)]
        else:
            cx=max(x1+55,min(x2-55,tx)); pts=[(cx-24,y1+6),(cx+24,y1+6),(cx,y1-48)]
        draw.polygon(pts, fill=fill, outline=stroke)
        draw.line([pts[0],pts[2],pts[1]], fill=stroke, width=5)
    draw_wrapped(draw,(x1+28,y1+22),text,f,max_w or (x2-x1-56),line_h=int(f.size*1.32),align=align)

def caption(draw, box, text, fill=(20,20,20), color=(255,255,255), f=None):
    f=f or F['black']; x1,y1,x2,y2=box
    draw.rounded_rectangle(box, radius=8, fill=fill)
    draw_wrapped(draw,(x1+22,y1+18),text,f,fill=color,max_w=x2-x1-44,line_h=int(f.size*1.25),align='center')

def phone(draw,x,y,w,h):
    draw.rounded_rectangle((x,y,x+w,y+h), radius=30, fill=(35,35,35), outline=(0,0,0), width=5)
    draw.rounded_rectangle((x+18,y+28,x+w-18,y+h-28), radius=18, fill=(248,250,252), outline=(180,180,180), width=2)

def laptop(draw,x,y,w,h):
    draw.rounded_rectangle((x,y,x+w,y+h), radius=12, fill=(230,236,245), outline=(20,20,20), width=5)
    draw.rectangle((x+18,y+18,x+w-18,y+h-18), fill=(255,255,255), outline=(120,120,120), width=2)
    draw.polygon([(x-40,y+h),(x+w+40,y+h),(x+w+80,y+h+45),(x-80,y+h+45)], fill=(170,180,195), outline=(20,20,20))

def bg_speed(draw, box, color=(220,230,255)):
    x1,y1,x2,y2=box
    for i in range(28):
        x=x1+i*(x2-x1)//28
        draw.line((x,y1,x+(x2-x1)//4,y2), fill=color, width=3)

def page_base():
    img=Image.new('RGB',(W,H),(245,242,235)); d=ImageDraw.Draw(img)
    return img,d

def save(img,n):
    img.save(OUT/f'{n:02d}.png', quality=95)

# Page 1
img,d=page_base(); panel(d,(40,40,1040,610),fill=(255,255,255)); bg_speed(d,(40,40,1040,610)); person(d,230,500,1.25,'hero','worried'); laptop(d,520,250,390,230)
speech(d,(410,85,980,260),'ChatGPTもGeminiも\n使ってる。',F['bubble'],tail=(295,330))
speech(d,(470,335,1010,535),'でも、納品できる形に\nするところで止まる。',F['bubble'],tail=(295,380))
panel(d,(40,650,1040,1120),fill=(20,24,33)); draw_wrapped(d,(95,725),'AIを使っている。\nなのに、仕事になっていない。',F['title'],fill=(255,255,255),max_w=890,line_h=86,align='center'); caption(d,(90,960,990,1080),'Claude Code / Codex時代、\nもう“文章だけAI”では足りない。',fill=(255,230,95),color=(10,10,10),f=F['black'])
panel(d,(40,1160,1040,1710),fill=(255,255,255)); person(d,500,1550,1.35,'hero','normal'); draw_wrapped(d,(100,1220),'ツギノメAI実務スクール',F['h'],max_w=880,align='center'); draw_wrapped(d,(105,1320),'フリーランスがAIを\n仕事に変えるための実践講座',F['body'],max_w=870,align='center')
d.rounded_rectangle((150,1740,930,1840),radius=50,fill=(6,199,85),outline=(15,15,15),width=6); draw_wrapped(d,(220,1765),'LINEで無料資料を受け取る',F['cta'],fill=(255,255,255),max_w=640,align='center')
save(img,1)

# Page 2
img,d=page_base(); panel(d,(40,40,1040,500)); phone(d,120,105,330,330); draw_wrapped(d,(180,165),'X',F['h'],max_w=210,align='center'); draw_wrapped(d,(480,95),'「Claude Codeで\n制作が変わる」\n「Codexで実装スピードが変わる」\n「AIに作らせる人が増えている」',F['body'],max_w=500,line_h=58)
panel(d,(40,540,1040,1060)); person(d,240,940,1.25,'hero','worried'); speech(d,(390,610,1000,810),'名前は知ってる。\nでも、正直こわい。',F['bubble'],tail=(275,775)); speech(d,(440,850,1000,1015),'エンジニアじゃない私に\n関係あるの？',F['bubble'],tail=(285,855))
panel(d,(40,1100,1040,1540),fill=(248,250,252)); laptop(d,120,1210,360,230); draw_wrapped(d,(545,1185),'便利なAIを\n知っているだけでは、',F['body'],max_w=390,align='center'); draw_wrapped(d,(510,1345),'置いていかれる\n気がする。',F['h'],fill=(180,40,40),max_w=450,align='center')
panel(d,(40,1580,1040,1870),fill=(17,24,39)); draw_wrapped(d,(90,1650),'最初の一歩が、重い。',F['title'],fill=(255,255,255),max_w=900,align='center')
save(img,2)

# Page3
img,d=page_base(); panel(d,(40,40,1040,520),fill=(255,250,250)); draw_wrapped(d,(95,85),'AI副業スクール広告',F['h'],max_w=890,align='center'); caption(d,(120,190,960,310),'「誰でも簡単！」\n「AI副業で月収◯◯万円！」',fill=(230,60,60),color=(255,255,255),f=F['black']); person(d,210,500,0.85,'hero','worried'); speech(d,(400,355,960,485),'こういうのは無理。',F['bubble'],tail=(245,410))
panel(d,(40,560,1040,1010)); person(d,250,900,1.0,'hero','normal'); phone(d,575,620,260,330); speech(d,(90,615,520,770),'でも、無料資料だけなら\n見てもいいかも。',F['bubble'],tail=(245,755)); draw_wrapped(d,(610,720),'LINE',F['h'],fill=(6,160,75),max_w=180,align='center')
panel(d,(40,1050,1040,1810),fill=(255,255,255)); draw_wrapped(d,(90,1115),'AI実務化\nスターターキット',F['title'],max_w=900,align='center'); items=['1. Claude Code / Codex\n   最初の一歩テンプレ','2. AIを納品物に変える\n   ロードマップ','3. 提出前チェックリスト']
y=1320
for it in items:
    d.rounded_rectangle((120,y,960,y+130),radius=22,fill=(239,246,255),outline=(20,20,20),width=4)
    draw_wrapped(d,(155,y+20),it,F['body'],max_w=760,line_h=46)
    y+=155
save(img,3)

# Page4 online consult
img,d=page_base(); panel(d,(40,40,1040,520)); person(d,210,450,1.05,'hero','normal'); speech(d,(360,105,990,295),'無料相談があるなら、\n一回だけ聞いてみよう。',F['bubble'],tail=(250,290)); laptop(d,520,310,380,160)
panel(d,(40,560,1040,1280),fill=(244,248,255)); laptop(d,140,650,800,430); # screen mentor
panel(d,(220,720,860,1015),fill=(230,236,250),width=4); draw_wrapped(d,(250,740),'オンライン個別相談',F['body'],max_w=580,align='center'); person(d,540,1035,0.68,'mentor','normal'); speech(d,(90,1160,990,1260),'いきなりオフラインではなく、まずオンラインで相談。',F['small'],align='center')
panel(d,(40,1320,1040,1840)); person(d,250,1770,1.0,'mentor','normal'); speech(d,(390,1370,1005,1535),'Claude CodeやCodexは、\nエンジニアだけのものでは\nありません。',F['small'],tail=(270,1600)); speech(d,(395,1580,1005,1775),'フリーランスが“作れる範囲”を\n広げるための武器です。',F['bubble'],tail=(275,1660)); speech(d,(70,1348,360,1460),'でも、コードは\n書けません。',F['small'],tail=(210,1580))
save(img,4)

# Page5 working tools
img,d=page_base(); panel(d,(40,40,1040,450)); person(d,220,390,1.0,'mentor','normal'); speech(d,(380,90,1000,230),'覚えるのは\nコード暗記ではありません。',F['bubble'],tail=(250,250)); speech(d,(420,260,1000,405),'AIに作らせて、確認して、\n直して、使う流れです。',F['bubble'],tail=(265,285))
panel(d,(40,490,1040,1260),fill=(248,250,252)); draw_wrapped(d,(90,540),'実際に動くツールとして使える',F['h'],max_w=900,align='center'); steps=[('LP改善案','診断フォーム'),('自動集計','提案資料')]
coords=[(110,690),(590,690),(110,970),(590,970)]
labels=['LP改善案','診断フォーム','自動集計','提案資料']
for i,(x,y) in enumerate(coords):
    d.rounded_rectangle((x,y,x+380,y+190),radius=18,fill=(255,255,255),outline=(20,20,20),width=5)
    draw_wrapped(d,(x+25,y+50),labels[i],F['body'],max_w=330,align='center')
# arrows
for (x1,y1),(x2,y2) in [((490,785),(590,785)),((300,880),(300,970)),((490,1065),(590,1065))]:
    d.line((x1,y1,x2,y2),fill=(20,20,20),width=8); d.polygon([(x2,y2),(x2-24,y2-14),(x2-24,y2+14)],fill=(20,20,20))
panel(d,(40,1300,1040,1840)); person(d,215,1760,1.0,'hero','smile'); speech(d,(360,1365,1000,1570),'触ってみたら、\n今の仕事で使えるアイデアが\n出てきそう…。',F['bubble'],tail=(250,1600)); caption(d,(365,1630,1000,1770),'“たたき台”で終わらせない。\n動くところまで。',fill=(255,230,95),color=(15,15,15),f=F['black'])
save(img,5)

# Page6 curriculum
img,d=page_base(); panel(d,(40,40,1040,310),fill=(17,24,39)); draw_wrapped(d,(90,90),'Claude Code / Codexを\n触れる側に回る4週間',F['h'],fill=(255,255,255),max_w=900,align='center')
weeks=[('Week1 Web','最初の壁を越える\n自分の仕事を分解'),('Week2 Web','資料・提案・LP改善に\nAIを入れる'),('Week3 Web','動くミニツールを作る'),('Week4 大阪','成果物レビュー\n納品品質チェック')]
y=370
for i,(w,t) in enumerate(weeks):
    fill=(255,255,255) if i%2==0 else (239,246,255)
    d.rounded_rectangle((90,y,990,y+245),radius=26,fill=fill,outline=(20,20,20),width=5)
    d.ellipse((125,y+55,245,y+175),fill=(255,230,95),outline=(20,20,20),width=4)
    draw_wrapped(d,(125,y+84),str(i+1),F['h'],max_w=120,align='center')
    draw_wrapped(d,(285,y+45),w,F['h'],max_w=640)
    draw_wrapped(d,(285,y+115),t,F['body'],max_w=640,line_h=48)
    y+=285
caption(d,(90,1550,990,1735),'いきなりオフラインではなく、\nまずはオンラインで安心して相談・参加。',fill=(6,199,85),color=(255,255,255),f=F['black'])
save(img,6)

# Page7 fit/not fit
img,d=page_base(); panel(d,(40,40,1040,180),fill=(17,24,39)); draw_wrapped(d,(90,72),'向いている人 / 向いていない人',F['h'],fill=(255,255,255),max_w=900,align='center')
panel(d,(60,230,1020,865),fill=(240,253,244)); draw_wrapped(d,(110,280),'向いている人',F['h'],fill=(6,120,60),max_w=860,align='center'); ok=['ChatGPTやGeminiは使っている','Claude Code / Codexに壁を感じている','今の仕事にAIを入れて提案範囲を広げたい','置いていかれる危機感がある']
y=380
for item in ok:
    draw_wrapped(d,(130,y),'✓ '+item,F['body'],max_w=830); y+=98
panel(d,(60,920,1020,1425),fill=(255,247,237)); draw_wrapped(d,(110,970),'向いていない人',F['h'],fill=(180,70,20),max_w=860,align='center'); ng=['誰でも簡単に稼ぎたい人','危機感がない人','案件保証だけを期待する人']
y=1080
for item in ng:
    draw_wrapped(d,(130,y),'× '+item,F['body'],max_w=830); y+=100
panel(d,(40,1480,1040,1860)); person(d,205,1790,0.95,'mentor','normal'); speech(d,(350,1530,1000,1705),'重要性に気づいていない人向けではありません。',F['bubble'],tail=(240,1660)); speech(d,(390,1725,1000,1840),'使えるフリーランスになりたい人向けです。',F['small'],tail=(250,1710))
save(img,7)

# Page8 final
img,d=page_base(); panel(d,(40,40,1040,520)); bg_speed(d,(40,40,1040,520),color=(235,235,235)); person(d,230,470,1.1,'hero','smile'); speech(d,(390,95,1005,245),'もう避けない。',F['bubble'],tail=(270,275)); speech(d,(390,280,1005,455),'まずは最初のハードルを越えて、\n触ってみる。',F['bubble'],tail=(280,350))
panel(d,(40,560,1040,1140),fill=(17,24,39)); draw_wrapped(d,(90,650),'フリーランスが\nClaude Code / Codex時代に\n置いていかれないために。',F['title'],fill=(255,255,255),max_w=900,line_h=82,align='center')
panel(d,(40,1180,1040,1690),fill=(255,255,255)); draw_wrapped(d,(100,1240),'LINE登録プレゼント',F['h'],max_w=880,align='center'); draw_wrapped(d,(100,1340),'AI実務化\nスターターキット',F['title'],fill=(6,120,80),max_w=880,align='center'); draw_wrapped(d,(135,1545),'Claude Code・Codex入門 / ロードマップ / 提出前チェックリスト',F['small'],max_w=810,align='center')
d.rounded_rectangle((150,1740,930,1840),radius=50,fill=(6,199,85),outline=(15,15,15),width=6); draw_wrapped(d,(220,1765),'LINEで無料資料を受け取る',F['cta'],fill=(255,255,255),max_w=640,align='center')
save(img,8)

print('generated', len(list(OUT.glob('*.png'))), 'pages in', OUT)
