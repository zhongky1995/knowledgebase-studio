#!/usr/bin/env python3
"""Build editable diagram examples and a local comparison gallery (standard library only)."""
import argparse
from html import escape
from pathlib import Path

TEXT = '#172B4D'
MUTED = '#42526E'
BLUE = '#175CD3'
GREEN = '#067647'
AMBER = '#92400E'


def label(x, y, text, size=18, color=TEXT, anchor='start', weight=400):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{weight}">{escape(text)}</text>'


def box(x, y, w, h, fill='#F5F7FA', stroke='#B8C4D4', radius=12):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'


def arrow(d, color=BLUE, dashed=False):
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2.5" marker-end="url(#{"green" if color==GREEN else "blue"})"'+(' stroke-dasharray="6 5"' if dashed else '')+'/>'


def frame(title, desc, body):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 500" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">{escape(desc)}</desc>
<defs><marker id="blue" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10Z" fill="{BLUE}"/></marker><marker id="green" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10Z" fill="{GREEN}"/></marker></defs>
<rect width="360" height="500" fill="white"/>
<g font-family="system-ui, -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif">
{label(24,42,title,24,weight=650)}{body}
</g></svg>'''


def examples():
    before = ''
    for y, heading, saved in [(98,'收藏前',False),(270,'收藏后',True)]:
        before += box(24,y,312,144) + label(40,y+32,heading,20,weight=650)
        before += label(40,y+67,'页面',18,MUTED)
        before += f'<path d="M287 {y+47} l6 13 15 2 -11 10 3 15 -13 -7 -13 7 3 -15 -11 -10 15 -2Z" fill="{"#FEF0C7" if saved else "white"}" stroke="{AMBER if saved else MUTED}" stroke-width="2"/>'
        before += label(40,y+112,'记录',18,MUTED)+box(94,y+86,222,38,'#ECFDF3' if saved else 'white',GREEN if saved else '#B8C4D4',6)
        before += label(108,y+112,'新增：文章 A' if saved else '还没有收藏',18,GREEN if saved else MUTED)
    before += arrow('M180 244 V267')+label(24,461,'网站保存记录，页面显示已收藏。',18)
    flow = box(24,88,118,58)+box(218,88,118,58)+label(83,124,'浏览器',20,anchor='middle',weight=600)+label(277,124,'网站',20,anchor='middle',weight=600)
    flow += '<path d="M83 146 V406 M277 146 V406" stroke="#B8C4D4" stroke-width="2"/>'
    flow += label(180,187,'① 请求：查看订单',18,BLUE,'middle')+arrow('M83 207 H277')
    flow += box(202,230,134,54,'#F5F7FA')+label(269,264,'核对账号',18,anchor='middle')
    flow += label(180,321,'② 回复：订单内容',18,GREEN,'middle')+arrow('M277 340 H83',GREEN)
    flow += label(24,445,'网站核对账号后，再返回订单。',18)+label(24,475,'箭头表示传递方向，不表示耗时。',18,MUTED)
    shared = ''
    for x,t in [(24,'手机'),(204,'电脑')]:
        shared += box(x,98,132,104,'white',MUTED,9)+label(x+66,137,t,20,anchor='middle',weight=600)+label(x+66,172,'账号：小林',18,anchor='middle')
    shared += arrow('M90 204 V292')+arrow('M270 204 V292')
    shared += label(180,268,'请求收藏',18,BLUE,'middle')
    shared += box(24,292,312,138,'#ECFDF3',GREEN)+label(42,326,'网站保存的记录',20,GREEN,weight=600)
    shared += box(42,348,276,52,'white',GREEN,6)+label(54,381,'小林  /  文章 A  /  已收藏',18)
    shared += label(24,471,'边框表示存放位置；回复未画出。',18,MUTED)
    branch = box(24,89,312,64,'#F5F7FA')+label(180,129,'记录保存在哪里？',20,anchor='middle',weight=600)
    branch += arrow('M180 155 V180 H85 V220')+arrow('M180 180 H275 V220')
    branch += box(24,220,130,80,'white',BLUE)+box(206,220,130,80,'#ECFDF3',GREEN)
    branch += label(89,253,'仅原设备',20,anchor='middle',weight=600)+label(89,281,'本地保存',18,MUTED,'middle')
    branch += label(271,253,'网站',20,anchor='middle',weight=600)+label(271,281,'按账号保存',18,GREEN,'middle')
    branch += arrow('M89 302 V346')+arrow('M271 302 V346',GREEN)
    branch += label(89,375,'新设备没有',18,anchor='middle')+label(271,375,'可请求取回',18,GREEN,'middle')
    branch += label(24,437,'比较条件：换设备，登录同一账号。',18)+label(24,468,'假设没有其他备份或同步机制。',18,MUTED)
    specs = [
        ('before-after','收藏改变了什么？','收藏前没有记录、星星未亮；收藏后增加文章记录，星星亮起。',before,'同样的位置呈现同样的对象；新增记录与星标变化一一对应。','两段定义被装进方框，看不到收藏前后的记录变化。'),
        ('request-reply','请求和回复分别传递','浏览器向网站请求订单；网站核对账号后，把订单回复给浏览器。',flow,'两条箭头分别标明请求和回复，接收对象与先后顺序可见。','箭头没有标注传递内容，交叉线和大段文字遮住过程。'),
        ('shared-boundary','两台设备读同一份记录','手机和电脑使用同一账号向网站请求收藏；网站保管一份账号收藏记录。',shared,'设备分开，记录集中；边框明确表示记录存放位置。','多个重复盒子混在一起，无法判断记录是共享还是复制。'),
        ('condition-branch','换设备后能否找回？','只在原设备保存的记录不能由新设备直接取得；网站按账号保存时，新设备可请求取回。',branch,'固定换设备和同一账号的条件，再比较两种保存位置的结果。','颜色承担全部分类含义，分支没有条件或结果说明。'),
    ]
    output={};cards=[]
    for key,title,desc,good,why,problem in specs:
        output[key+'.svg']=frame(title,desc,good)
        bad=''
        for i in range(3):
            y=94+i*100
            bad+=box(24,y,312,78,'#F5F7FA','#DDE3EA')
            bad+=label(36,y+28,['状态生命周期与归属管理','跨层级协作与信息表达','持久化反馈及边界一致性'][i],16,'#9CA3AF')
            bad+=label(36,y+51,'执行处理、协调状态并完成系统闭环。',13,'#9CA3AF')
            if i<2: bad+=arrow(f'M180 {y+80} V{y+99}')
        if key == 'request-reply':
            bad = box(24,110,115,100)+box(221,110,115,100)+label(82,160,'客户端',16,anchor='middle')+label(278,160,'服务端',16,anchor='middle')
            bad += arrow('M139 130 L221 190')+arrow('M221 130 L139 190')
            bad += label(24,292,'跨层协作、传输处理、状态回传。',14,'#9CA3AF')
            bad += label(24,318,'请求响应过程实现信息表达与交付。',14,'#9CA3AF')
        elif key == 'shared-boundary':
            bad = box(24,100,312,310,'#F5F7FA','#DDE3EA')
            for y,t in [(124,'手机状态'),(215,'电脑状态'),(306,'共享状态')]:
                bad += box(48,y,264,65,'white','#DDE3EA')+label(180,y+40,t,16,'#9CA3AF','middle')
        elif key == 'condition-branch':
            bad = box(100,110,160,65)+label(180,150,'数据持久化',16,anchor='middle')
            bad += arrow('M180 177 V220 H80 V260')+arrow('M180 220 H280 V260')
            bad += box(24,260,120,80,'#FEE4E2','#B42318')+box(216,260,120,80,'#DCFAE6',GREEN)
            bad += label(24,411,'不同状态会影响系统最终的结果。',14,'#9CA3AF')
        # Counterexamples deliberately fail readability/meaning checks; exclude from manifests.
        output[key+'-bad.svg']=frame(title,'反例：段落被装进同样的方框，缺少具体对象与关系。',bad)
        cards.append(f'''<section><div class="section-head"><span class="number">0{len(cards)+1}</span><div><h2>{escape(title)}</h2><p>{escape(desc)}</p></div></div><div class="pair"><figure class="bad"><figcaption>反例 · 文字代替关系</figcaption><img src="{key}-bad.svg" alt="{escape(problem)}"/><p>{escape(problem)}</p></figure><figure class="good"><figcaption>改进 · 对象与变化可见</figcaption><img src="{key}.svg" alt="{escape(desc)}"/><p>{escape(why)}</p><a href="{key}.svg" download>下载可编辑 SVG</a></figure></div></section>''')
    output['index.html']='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>知识库图解 · 设计样例</title><style>
*{box-sizing:border-box}body{margin:0;background:#F5F7FA;color:#172B4D;font:17px/1.65 system-ui,-apple-system,"PingFang SC",sans-serif}main{max-width:1000px;margin:auto;padding:48px 24px}header{max-width:760px;margin-bottom:40px}.eyebrow{color:#175CD3;font-size:14px;font-weight:650;letter-spacing:.12em}h1{font-size:36px;line-height:1.25;letter-spacing:-.03em;margin:12px 0 20px}h2{font-size:23px;line-height:1.4;margin:0}p{margin:10px 0;color:#42526E}section{margin:0 0 44px}.section-head{display:flex;gap:16px;align-items:flex-start;margin:0 0 16px}.number{font-size:18px;color:#175CD3;font-weight:600;padding-top:3px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:20px}figure{margin:0;background:white;border:1px solid #CDD5DF;border-radius:16px;overflow:hidden;min-width:0}figcaption{padding:16px 20px;font-weight:650;font-size:16px;border-bottom:1px solid #E4E7EC}.good figcaption{color:#067647;background:#ECFDF3}.bad figcaption{color:#92400E;background:#FFFAEB}img{display:block;width:100%;max-width:360px;height:auto;margin:auto}figure p{margin:12px 20px;font-size:16px}a{display:inline-block;color:#175CD3;margin:0 20px 20px}footer{border-top:1px solid #CDD5DF;padding-top:20px;font-size:15px}button{font:inherit;color:#172B4D;background:white;border:1px solid #98A2B3;padding:8px 14px;border-radius:8px;cursor:pointer}button:focus-visible,a:focus-visible{outline:3px solid #175CD3;outline-offset:3px}.gray img{filter:grayscale(1)}@media(max-width:640px){main{padding:28px 12px}h1{font-size:28px}.pair{grid-template-columns:1fr;gap:16px}h2{font-size:21px}header{margin-bottom:32px}}
</style><main><header><div class="eyebrow">KNOWLEDGEBASE STUDIO / VISUAL PATTERNS</div><h1>让关系可见，<br>让文字回到解释的位置。</h1><p>四种可复用图型，把“发生了什么”画出来。每组使用同一问题，对照文字堆叠与机制表达。示例均为虚构教学情境。</p><button type="button" aria-pressed="false" onclick="document.body.classList.toggle('gray');this.setAttribute('aria-pressed',document.body.classList.contains('gray'))">切换灰度检查</button></header>'''+''.join(cards)+'''<footer>使用方法：选择符合问题的图型，下载并修改对象、文字和关系，再在实际文章里验证。反例用于审读训练，不属于可发布素材。图型不替代事实核验；编辑审读也不代表真实读者已理解。</footer></main></html>'''
    return output


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--force',action='store_true',help='Replace only known generated example files.')
    args=parser.parse_args()
    files=examples()
    if any((args.output/name).exists() for name in files) and not args.force:
        parser.error('Example files exist; choose a new directory or use --force.')
    args.output.mkdir(parents=True,exist_ok=True)
    for name,body in files.items():
        (args.output/name).write_text(body+'\n',encoding='utf-8')
    print(f'Created {len(files)} files in {args.output.resolve()}')


if __name__=='__main__':
    main()
