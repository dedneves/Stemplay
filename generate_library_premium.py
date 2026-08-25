#!/usr/bin/env python3
"""
StemPlay Library Premium v3
- Interface refinada (glassmorphism + gradientes)
- Botoes Online + Download em cada card
- Busca, filtros, favoritos, dark/light, bottom nav mobile
"""

import re, json
from pathlib import Path
from collections import defaultdict

READER_BASE = "https://reader.stemplay.io/?file="
USER_ID = "k3s"

def parse_pdf_info(url):
    filename = url.split("/")[-1].replace(".pdf", "")
    parts = url.split("/")
    course_raw = parts[4] if len(parts) > 4 else "OUTROS"
    course = course_raw.replace("-", " ").replace("_", " ").title()

    is_teacher = "TEACHER" in filename.upper()
    is_student = "STUDENT" in filename.upper()
    is_workbook = "WORKBOOK" in filename.upper()
    material_type = "Teacher" if is_teacher else ("Workbook" if is_workbook else ("Student" if is_student else "Standard"))

    lesson_match = re.search(r'(?:Aula|Lesson|Class)(\d+)', filename, re.IGNORECASE)
    unit_match = re.search(r'Unit(\d+)', filename)
    module_match = re.search(r'M(\d+)', filename)

    lesson_num = int(lesson_match.group(1)) if lesson_match else None
    unit_num = int(unit_match.group(1)) if unit_match else None
    module_num = int(module_match.group(1)) if module_match else None

    if lesson_num:
        display_name = f"Aula {lesson_num:02d}"
    elif unit_num:
        display_name = f"Unidade {unit_num:02d}"
    elif module_num:
        display_name = f"Módulo {module_num}"
    else:
        display_name = filename.replace("_", " ").replace("-", " ")

    if module_num and lesson_num:
        sort_key = (module_num, lesson_num, 0)
        group_name = f"Módulo {module_num}"
    elif unit_num:
        sort_key = (unit_num, 0, 0)
        group_name = "Unidades"
    else:
        sort_key = (0, 0, 0)
        group_name = "Geral"

    return {
        "url": url, "course": course, "course_raw": course_raw,
        "display_name": display_name, "material_type": material_type,
        "lesson_num": lesson_num, "unit_num": unit_num, "module_num": module_num,
        "sort_key": sort_key, "group_name": group_name
    }

def main():
    input_file = "pdfs_found.txt"
    output_html = "stemplay_library.html"

    if not Path(input_file).exists():
        print(f"❌ {input_file} não encontrado! Rode s3_god_mode.py primeiro.")
        return

    print("📖 Carregando PDFs...")
    with open(input_file, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    print(f"🔍 Parseando {len(urls)} arquivos...")
    pdfs = [parse_pdf_info(url) for url in urls]

    courses_dict = defaultdict(list)
    for pdf in pdfs:
        courses_dict[pdf['course']].append(pdf)

    courses = [{"name": n, "items": sorted(it, key=lambda x: x['sort_key'])}
               for n, it in sorted(courses_dict.items())]

    courses_json = json.dumps(courses, ensure_ascii=False)
    print("🎨 Gerando biblioteca premium v3...")

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0a0a1a">
<meta name="apple-mobile-web-app-capable" content="yes">
<title>StemPlay Library</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📚</text></svg>">
<style>
*{{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}}
:root{{--bg:#0a0a1a;--bg2:#12122a;--bg3:#1a1a3e;--accent:#6c5ce7;--accent2:#a29bfe;--glow:rgba(108,92,231,.25);--txt:#f0f0ff;--txt2:#8888aa;--card:rgba(26,26,62,.6);--border:#2a2a5e;--ok:#00cec9;--warn:#fdcb6e;--danger:#ff7675;--radius:16px}}
html[data-theme="light"]{{--bg:#f4f6fb;--bg2:#ffffff;--bg3:#e8ecf5;--accent:#6c5ce7;--accent2:#5a4bd1;--glow:rgba(108,92,231,.15);--txt:#1a1a2e;--txt2:#666;--card:rgba(255,255,255,.8);--border:#dde1ea}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--txt);min-height:100vh;padding-bottom:75px;transition:background .3s,color .3s}}
.header{{position:sticky;top:0;background:var(--bg2);border-bottom:1px solid var(--border);z-index:100;backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px)}}
.header-top{{display:flex;align-items:center;justify-content:space-between;padding:1rem 1.25rem}}
.logo{{font-size:1.4rem;font-weight:900;background:linear-gradient(135deg,var(--accent),#fd79a8);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;letter-spacing:-.5px}}
.theme-btn{{width:42px;height:42px;border-radius:50%;background:var(--bg3);border:none;color:var(--txt);cursor:pointer;font-size:1.2rem;display:flex;align-items:center;justify-content:center;transition:transform .2s}}
.theme-btn:active{{transform:scale(.85)}}
.stats-row{{display:flex;gap:.5rem;padding:0 1.25rem .75rem;overflow-x:auto;scrollbar-width:none}}
.stats-row::-webkit-scrollbar{{display:none}}
.chip{{background:var(--bg3);padding:.35rem .85rem;border-radius:20px;font-size:.75rem;white-space:nowrap;border:1px solid var(--border);flex-shrink:0}}
.chip b{{color:var(--accent2);margin-right:.25rem}}
.search-wrap{{padding:0 1.25rem .75rem}}
.search{{width:100%;padding:.9rem 1.1rem;background:var(--bg3);border:2px solid var(--border);border-radius:var(--radius);color:var(--txt);font-size:1rem;transition:border .2s,box-shadow .2s}}
.search:focus{{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px var(--glow)}}
.filters{{display:flex;gap:.4rem;padding:0 1.25rem 1rem;overflow-x:auto;scrollbar-width:none}}
.filters::-webkit-scrollbar{{display:none}}
.fbtn{{padding:.45rem 1rem;background:var(--bg3);border:1.5px solid var(--border);border-radius:20px;color:var(--txt2);cursor:pointer;font-weight:600;font-size:.8rem;white-space:nowrap;transition:all .2s;flex-shrink:0}}
.fbtn.active{{background:var(--accent);border-color:var(--accent);color:#fff}}
.main{{padding:0 .75rem;max-width:1400px;margin:0 auto}}
.course{{background:var(--bg2);border-radius:var(--radius);margin-bottom:.75rem;border:1px solid var(--border);overflow:hidden}}
.chdr{{padding:1rem 1.25rem;cursor:pointer;display:flex;justify-content:space-between;align-items:center;user-select:none;transition:background .15s}}
.chdr:active{{background:var(--bg3)}}
.ctitle{{font-size:1rem;font-weight:700;flex:1;margin-right:.5rem;line-height:1.3}}
.ccount{{background:var(--accent);color:#fff;padding:.2rem .65rem;border-radius:12px;font-size:.7rem;font-weight:800;flex-shrink:0}}
.carrow{{color:var(--txt2);transition:transform .3s;font-size:1rem;margin-left:.5rem}}
.course.open .carrow{{transform:rotate(180deg)}}
.cbody{{display:none;padding:0 1.25rem 1.25rem;animation:fadeIn .25s ease}}
.course.open .cbody{{display:block}}
@keyframes fadeIn{{from{{opacity:0;transform:translateY(-8px)}}to{{opacity:1;transform:translateY(0)}}}}
.gtitle{{color:var(--accent2);font-size:.8rem;font-weight:700;margin:.85rem 0 .5rem;text-transform:uppercase;letter-spacing:.5px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:.6rem}}
.card{{background:var(--card);backdrop-filter:blur(10px);border-radius:var(--radius);padding:1rem;text-decoration:none;color:var(--txt);border:1.5px solid var(--border);display:flex;flex-direction:column;gap:.6rem;transition:transform .15s,border-color .2s,box-shadow .2s;position:relative;overflow:hidden}}
.card::before{{content:'';position:absolute;top:0;left:0;width:100%;height:3px;background:linear-gradient(90deg,var(--accent),var(--accent2))}}
.card.teacher::before{{background:linear-gradient(90deg,var(--warn),#e17055)}}
.card.workbook::before{{background:linear-gradient(90deg,var(--ok),#55efc4)}}
.card:active{{transform:scale(.97)}}
.card-top{{display:flex;align-items:center;gap:.75rem}}
.card-icon{{font-size:1.6rem;flex-shrink:0}}
.card-info{{flex:1;min-width:0}}
.card-name{{font-weight:700;font-size:.95rem;margin-bottom:.2rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.card-badges{{display:flex;gap:.3rem;flex-wrap:wrap}}
.badge{{padding:.15rem .55rem;border-radius:10px;font-size:.6rem;font-weight:800;text-transform:uppercase;letter-spacing:.3px}}
.b-teacher{{background:var(--warn);color:#1a1a2e}}
.b-workbook{{background:var(--ok);color:#1a1a2e}}
.b-student,.b-standard{{background:var(--accent);color:#fff}}
.card-actions{{display:flex;gap:.4rem;margin-top:.25rem}}
.abtn{{flex:1;padding:.55rem;border:none;border-radius:10px;font-size:.75rem;font-weight:700;cursor:pointer;text-align:center;text-decoration:none;display:flex;align-items:center;justify-content:center;gap:.3rem;transition:all .15s;color:inherit}}
.abtn:active{{transform:scale(.95)}}
.btn-online{{background:var(--accent);color:#fff}}
.btn-dl{{background:var(--bg3);color:var(--txt);border:1.5px solid var(--border)}}
.btn-fav{{background:none;border:1.5px solid var(--border);color:var(--txt2);width:40px;flex:none;font-size:1.1rem;border-radius:10px}}
.btn-fav.is-fav{{color:var(--warn);border-color:var(--warn)}}
.bottom-nav{{position:fixed;bottom:0;left:0;right:0;background:var(--bg2);border-top:1px solid var(--border);display:flex;justify-content:space-around;padding:.4rem 0 calc(.4rem + env(safe-area-inset-bottom));z-index:100;backdrop-filter:blur(20px)}}
.nitem{{background:none;border:none;color:var(--txt2);padding:.4rem .8rem;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:.15rem;font-size:.65rem;font-weight:600;transition:color .2s}}
.nitem.active{{color:var(--accent)}}
.nicon{{font-size:1.4rem}}
.toast{{position:fixed;bottom:85px;left:50%;transform:translateX(-50%);background:var(--bg2);color:var(--txt);padding:.7rem 1.3rem;border-radius:25px;box-shadow:0 8px 30px rgba(0,0,0,.3);z-index:1000;opacity:0;transition:opacity .3s;pointer-events:none;border:1px solid var(--border);font-size:.85rem;font-weight:600}}
.toast.show{{opacity:1}}
.empty{{text-align:center;padding:4rem 1rem;color:var(--txt2)}}
.empty-icon{{font-size:4rem;margin-bottom:1rem}}
@media(min-width:768px){{body{{padding-bottom:0}}.bottom-nav{{display:none}}.main{{padding:0 2rem}}.grid{{grid-template-columns:repeat(auto-fill,minmax(300px,1fr))}}.card:hover{{transform:translateY(-3px);border-color:var(--accent);box-shadow:0 8px 25px var(--glow)}}}}
@media(max-width:480px){{.grid{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<div class="header">
  <div class="header-top">
    <div class="logo">📚 StemPlay Library</div>
    <button class="theme-btn" id="themeBtn" title="Tema">🌓</button>
  </div>
  <div class="stats-row">
    <div class="chip"><b id="sT">0</b>materiais</div>
    <div class="chip"><b id="sC">0</b>cursos</div>
    <div class="chip"><b id="sV">0</b>visíveis</div>
  </div>
  <div class="search-wrap">
    <input type="text" class="search" id="searchBox" placeholder="🔍 Buscar curso, aula, módulo..." autocomplete="off">
  </div>
  <div class="filters" id="filterBar">
    <button class="fbtn active" data-t="all">Todos</button>
    <button class="fbtn" data-t="Standard">📖 Padrão</button>
    <button class="fbtn" data-t="Teacher">👨‍🏫 Teacher</button>
    <button class="fbtn" data-t="Workbook">📝 Workbook</button>
    <button class="fbtn" data-t="Student">🎓 Student</button>
  </div>
</div>
<div class="main" id="app"></div>
<div class="bottom-nav">
  <button class="nitem active" data-a="home"><span class="nicon">🏠</span>Início</button>
  <button class="nitem" data-a="courses"><span class="nicon">📚</span>Cursos</button>
  <button class="nitem" data-a="fav"><span class="nicon">⭐</span>Favoritos</button>
  <button class="nitem" data-a="top"><span class="nicon">⬆️</span>Topo</button>
</div>
<div class="toast" id="toast"></div>
<script>
const D={courses_json};
let cF='all',cS='',cV='home';
let favs=JSON.parse(localStorage.getItem('sp_favs')||'[]');
const $=id=>document.getElementById(id);
const $$=(s,p)=>(p||document).querySelectorAll(s);
function toast(m){{const t=$('toast');t.textContent=m;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2200)}}
async function downloadPDF(url,name){{
  try{{
    toast('⬇️ Baixando...');
    const r=await fetch(url);
    if(!r.ok)throw 0;
    const b=await r.blob();
    const a=document.createElement('a');
    a.href=URL.createObjectURL(b);
    a.download=name+'.pdf';
    document.body.appendChild(a);a.click();a.remove();
    toast('✅ Download iniciado!');
  }}catch(e){{
    window.open(url,'_blank');
    toast('📄 Aberto em nova aba');
  }}
}}
function render(){{
  const app=$('app');app.innerHTML='';let vc=0;const sl=cS.toLowerCase();
  D.forEach(c=>{{
    const fi=c.items.filter(i=>{{
      const ms=!sl||i.course.toLowerCase().includes(sl)||i.display_name.toLowerCase().includes(sl)||i.group_name.toLowerCase().includes(sl);
      const mf=cF==='all'||i.material_type===cF;
      if(cV==='fav')return favs.includes(i.url);
      return ms&&mf;
    }});
    if(!fi.length)return;vc+=fi.length;
    const gs={{}};fi.forEach(i=>{{(gs[i.group_name]=gs[i.group_name]||[]).push(i)}});
    const ce=document.createElement('div');ce.className='course';
    ce.innerHTML=`<div class="chdr"><div class="ctitle">${{c.name}}</div><div class="ccount">${{fi.length}}</div><div class="carrow">▼</div></div><div class="cbody"></div>`;
    const cb=ce.querySelector('.cbody');
    Object.entries(gs).forEach(([gn,items])=>{{
      const gt=document.createElement('div');gt.className='gtitle';gt.textContent=gn+' · '+items.length+' itens';cb.appendChild(gt);
      const gr=document.createElement('div');gr.className='grid';
      items.forEach(i=>{{
        const a=document.createElement('div');a.className='card '+i.material_type.toLowerCase();
        const ic=i.material_type==='Teacher'?'👨‍🏫':i.material_type==='Workbook'?'📝':i.material_type==='Student'?'🎓':'📖';
        const bc='b-'+i.material_type.toLowerCase();
        const isF=favs.includes(i.url);
        const onlineUrl='https://reader.stemplay.io/?file='+encodeURIComponent(i.url)+'&userId=k3s';
        let badges=`<span class="badge ${{bc}}">${{i.material_type}}</span>`;
        if(i.module_num)badges+=`<span class="badge" style="background:#8b5cf6;color:#fff">M${{i.module_num}}</span>`;
        if(i.unit_num)badges+=`<span class="badge" style="background:#ec4899;color:#fff">U${{i.unit_num}}</span>`;
        a.innerHTML=`<div class="card-top"><div class="card-icon">${{ic}}</div><div class="card-info"><div class="card-name">${{i.display_name}}</div><div class="card-badges">${{badges}}</div></div></div><div class="card-actions"><a href="${{onlineUrl}}" target="_blank" rel="noopener" class="abtn btn-online">🌐 Online</a><button class="abtn btn-dl" data-url="${{i.url}}" data-name="${{i.display_name}}">⬇️ Download</button><button class="abtn btn-fav${{isF?' is-fav':''}}" data-url="${{i.url}}">${{isF?'★':'☆'}}</button></div>`;
        a.querySelector('.btn-dl').onclick=e=>{{e.stopPropagation();downloadPDF(i.url,i.display_name)}};
        a.querySelector('.btn-fav').onclick=e=>{{e.stopPropagation();toggleFav(i.url)}};
        gr.appendChild(a);
      }});
      cb.appendChild(gr);
    }});
    ce.querySelector('.chdr').onclick=()=>ce.classList.toggle('open');
    app.appendChild(ce);
  }});
  $('sT').textContent=D.reduce((s,c)=>s+c.items.length,0);
  $('sC').textContent=D.length;$('sV').textContent=vc;
  if(!vc)app.innerHTML=`<div class="empty"><div class="empty-icon">${{cV==='fav'?'⭐':'🔍'}}</div><h3>${{cV==='fav'?'Nenhum favorito':'Nada encontrado'}}</h3><p style="margin-top:.5rem;font-size:.85rem;color:var(--txt2)">${{cV==='fav'?'Toque em ☆ para favoritar':'Tente outra busca'}}</p></div>`;
}}
function toggleFav(u){{const i=favs.indexOf(u);if(i>=0){{favs.splice(i,1);toast('Removido dos favoritos')}}else{{favs.push(u);toast('⭐ Favoritado!')}}localStorage.setItem('sp_favs',JSON.stringify(favs));render()}}
$('themeBtn').onclick=()=>{{const c=document.documentElement.getAttribute('data-theme');const n=c==='dark'?'light':'dark';document.documentElement.setAttribute('data-theme',n);localStorage.setItem('sp_theme',n);toast(n==='dark'?'🌙 Modo escuro':'☀️ Modo claro')}};
let st;
$('searchBox').oninput=e=>{{clearTimeout(st);st=setTimeout(()=>{{cS=e.target.value;render()}},180)}};
$('filterBar').onclick=e=>{{const b=e.target.closest('.fbtn');if(!b)return;$$('.fbtn').forEach(x=>x.classList.remove('active'));b.classList.add('active');cF=b.dataset.t;render()}};
$$('.nitem').forEach(b=>b.onclick=function(){{if(this.dataset.a==='top'){{window.scrollTo({{top:0,behavior:'smooth'}});return}}$$('.nitem').forEach(x=>x.classList.remove('active'));this.classList.add('active');cV=this.dataset.a;render()}});
document.documentElement.setAttribute('data-theme',localStorage.getItem('sp_theme')||'dark');
render();
console.log('📚 StemPlay Library v3 |',D.reduce((s,c)=>s+c.items.length,0),'materiais em',D.length,'cursos');
</script>
</body>
</html>"""

    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Biblioteca gerada: {output_html}")
    print(f"📊 {len(courses)} cursos | {len(pdfs)} materiais")
    print("🎯 Features: Download ⬇️ | Online 🌐 | Favoritos ⭐ | Dark/Light 🌓 | Busca 🔍 | Filtros | Mobile 📱")

if __name__ == "__main__":
    main()
