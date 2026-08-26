#!/usr/bin/env python3
"""
StemPlay Library Premium v7
Com animações suaves no site
"""
import re, json, sys
from pathlib import Path
from collections import defaultdict

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

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
        display_name = f"Modulo {module_num}"
    else:
        display_name = filename.replace("_", " ").replace("-", " ")

    if module_num and lesson_num:
        sort_key = (module_num, lesson_num, 0)
        group_name = f"Modulo {module_num}"
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
        print(f"  [ERRO] {input_file} nao encontrado!")
        return

    print("  [INFO] Carregando PDFs...")
    with open(input_file, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    print(f"  [INFO] Parseando {len(urls)} arquivos...")
    pdfs = [parse_pdf_info(url) for url in urls]

    courses_dict = defaultdict(list)
    for pdf in pdfs:
        courses_dict[pdf['course']].append(pdf)

    courses = [{"name": n, "items": sorted(it, key=lambda x: x['sort_key'])}
               for n, it in sorted(courses_dict.items())]

    courses_json = json.dumps(courses, ensure_ascii=False)
    print("  [INFO] Gerando biblioteca HTML...")

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0a0a1a">
<title>StemPlay Library</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}}
:root{{--bg:#0a0a1a;--bg2:#12122a;--bg3:#1a1a3e;--accent:#6c5ce7;--accent2:#a29bfe;--glow:rgba(108,92,231,.25);--txt:#f0f0ff;--txt2:#8888aa;--card:rgba(26,26,62,.6);--border:#2a2a5e;--ok:#00cec9;--warn:#fdcb6e;--radius:16px}}
html[data-theme="light"]{{--bg:#f4f6fb;--bg2:#fff;--bg3:#e8ecf5;--accent:#6c5ce7;--accent2:#5a4bd1;--glow:rgba(108,92,231,.15);--txt:#1a1a2e;--txt2:#666;--card:rgba(255,255,255,.8);--border:#dde1ea}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--txt);min-height:100vh;padding-bottom:75px;transition:background .3s,color .3s;overflow-x:hidden}}

/* Animacao de entrada */
@keyframes fadeInUp{{from{{opacity:0;transform:translateY(20px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes slideInLeft{{from{{opacity:0;transform:translateX(-20px)}}to{{opacity:1;transform:translateX(0)}}}}
@keyframes pulse{{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.05)}}}}
@keyframes shimmer{{0%{{background-position:-200% 0}}100%{{background-position:200% 0}}}}
@keyframes glow{{0%,100%{{box-shadow:0 0 5px var(--glow)}}50%{{box-shadow:0 0 20px var(--glow),0 0 30px var(--glow)}}}}

.header{{position:sticky;top:0;background:var(--bg2);border-bottom:1px solid var(--border);z-index:100;backdrop-filter:blur(20px);animation:fadeInUp .5s ease}}
.header-top{{display:flex;align-items:center;justify-content:space-between;padding:1rem 1.25rem}}
.logo{{font-size:1.4rem;font-weight:900;background:linear-gradient(135deg,var(--accent),#fd79a8);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;letter-spacing:-.5px;animation:pulse 3s ease-in-out infinite}}
.theme-btn{{width:42px;height:42px;border-radius:50%;background:var(--bg3);border:1px solid var(--border);color:var(--txt);cursor:pointer;font-size:.8rem;font-weight:700;display:flex;align-items:center;justify-content:center;transition:all .3s ease}}
.theme-btn:hover{{transform:rotate(180deg) scale(1.1);border-color:var(--accent)}}
.theme-btn:active{{transform:scale(.85)}}
.stats-row{{display:flex;gap:.5rem;padding:0 1.25rem .75rem;overflow-x:auto;scrollbar-width:none}}
.stats-row::-webkit-scrollbar{{display:none}}
.chip{{background:var(--bg3);padding:.35rem .85rem;border-radius:20px;font-size:.75rem;white-space:nowrap;border:1px solid var(--border);flex-shrink:0;animation:fadeInUp .5s ease backwards;transition:all .3s ease}}
.chip:nth-child(1){{animation-delay:.1s}}
.chip:nth-child(2){{animation-delay:.2s}}
.chip:nth-child(3){{animation-delay:.3s}}
.chip:hover{{transform:translateY(-2px);border-color:var(--accent)}}
.chip b{{color:var(--accent2);margin-right:.25rem}}
.search-wrap{{padding:0 1.25rem .75rem;animation:fadeInUp .5s ease .2s backwards}}
.search{{width:100%;padding:.9rem 1.1rem;background:var(--bg3);border:2px solid var(--border);border-radius:var(--radius);color:var(--txt);font-size:1rem;transition:all .3s ease}}
.search:focus{{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px var(--glow);animation:glow 2s ease-in-out infinite}}
.filters{{display:flex;gap:.4rem;padding:0 1.25rem 1rem;overflow-x:auto;scrollbar-width:none;animation:fadeInUp .5s ease .3s backwards}}
.filters::-webkit-scrollbar{{display:none}}
.fbtn{{padding:.45rem 1rem;background:var(--bg3);border:1.5px solid var(--border);border-radius:20px;color:var(--txt2);cursor:pointer;font-weight:600;font-size:.8rem;white-space:nowrap;transition:all .3s cubic-bezier(.4,0,.2,1);flex-shrink:0}}
.fbtn:hover{{transform:translateY(-2px);border-color:var(--accent)}}
.fbtn.active{{background:var(--accent);border-color:var(--accent);color:#fff;animation:pulse .3s ease}}
.main{{padding:0 .75rem;max-width:1400px;margin:0 auto}}
.course{{background:var(--bg2);border-radius:var(--radius);margin-bottom:.75rem;border:1px solid var(--border);overflow:hidden;animation:fadeInUp .5s ease backwards;transition:all .3s ease}}
.course:hover{{border-color:var(--accent);box-shadow:0 4px 20px var(--glow)}}
.chdr{{padding:1rem 1.25rem;cursor:pointer;display:flex;justify-content:space-between;align-items:center;user-select:none;transition:background .3s ease}}
.chdr:hover{{background:var(--bg3)}}
.chdr:active{{background:var(--bg3);transform:scale(.99)}}
.ctitle{{font-size:1rem;font-weight:700;flex:1;margin-right:.5rem;line-height:1.3}}
.ccount{{background:var(--accent);color:#fff;padding:.2rem .65rem;border-radius:12px;font-size:.7rem;font-weight:800;flex-shrink:0;animation:pulse 2s ease-in-out infinite}}
.carrow{{color:var(--txt2);transition:transform .4s cubic-bezier(.4,0,.2,1);font-size:1rem;margin-left:.5rem}}
.course.open .carrow{{transform:rotate(180deg)}}
.cbody{{display:none;padding:0 1.25rem 1.25rem;animation:fadeInUp .4s ease}}
.course.open .cbody{{display:block}}
.gtitle{{color:var(--accent2);font-size:.8rem;font-weight:700;margin:.85rem 0 .5rem;text-transform:uppercase;letter-spacing:.5px;animation:slideInLeft .4s ease}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:.7rem}}
.card{{background:var(--card);backdrop-filter:blur(10px);border-radius:var(--radius);color:var(--txt);border:1.5px solid var(--border);display:flex;flex-direction:column;overflow:hidden;animation:fadeInUp .5s ease backwards;transition:all .3s cubic-bezier(.4,0,.2,1)}}
.card:hover{{transform:translateY(-4px) scale(1.02);border-color:var(--accent);box-shadow:0 8px 30px var(--glow)}}
.card:active{{transform:scale(.97)}}
.thumb-wrap{{position:relative;width:100%;aspect-ratio:3/4;background:var(--bg3);overflow:hidden;border-bottom:1px solid var(--border)}}
.placeholder{{width:100%;height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:.5rem;position:relative;overflow:hidden;transition:all .3s ease}}
.card:hover .placeholder{{transform:scale(1.05)}}
.placeholder::before{{content:'';position:absolute;inset:0;opacity:.15;background:radial-gradient(circle at 30% 20%,rgba(255,255,255,.4),transparent 50%);animation:shimmer 3s linear infinite;background-size:200% 200%}}
.ph-letter{{font-size:4rem;font-weight:900;color:rgba(255,255,255,.9);text-shadow:0 2px 20px rgba(0,0,0,.3);letter-spacing:-2px;z-index:1;transition:all .3s ease}}
.card:hover .ph-letter{{transform:scale(1.1) rotate(-5deg)}}
.ph-type{{font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:2px;color:rgba(255,255,255,.85);padding:.25rem .6rem;border-radius:10px;background:rgba(0,0,0,.25);backdrop-filter:blur(10px);z-index:1}}
.ph-course{{position:absolute;bottom:.5rem;left:.5rem;right:.5rem;font-size:.65rem;color:rgba(255,255,255,.8);font-weight:600;text-align:center;z-index:1;text-shadow:0 1px 3px rgba(0,0,0,.5);line-height:1.2;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.card-body{{padding:.85rem 1rem;display:flex;flex-direction:column;gap:.5rem;flex:1}}
.card-name{{font-weight:700;font-size:.9rem;line-height:1.3;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.card-badges{{display:flex;gap:.3rem;flex-wrap:wrap}}
.badge{{padding:.15rem .55rem;border-radius:10px;font-size:.6rem;font-weight:800;text-transform:uppercase;letter-spacing:.3px;transition:all .2s ease}}
.badge:hover{{transform:scale(1.1)}}
.b-teacher{{background:var(--warn);color:#1a1a2e}}
.b-workbook{{background:var(--ok);color:#1a1a2e}}
.b-student,.b-standard{{background:var(--accent);color:#fff}}
.card-actions{{display:flex;gap:.35rem;margin-top:auto}}
.abtn{{flex:1;padding:.55rem;border:none;border-radius:10px;font-size:.75rem;font-weight:700;cursor:pointer;text-align:center;text-decoration:none;display:flex;align-items:center;justify-content:center;gap:.3rem;transition:all .2s cubic-bezier(.4,0,.2,1);color:inherit;position:relative;overflow:hidden}}
.abtn::after{{content:'';position:absolute;inset:0;background:linear-gradient(45deg,transparent 30%,rgba(255,255,255,.3) 50%,transparent 70%);transform:translateX(-100%);transition:transform .6s ease}}
.abtn:hover::after{{transform:translateX(100%)}}
.abtn:active{{transform:scale(.95)}}
.btn-online{{background:var(--accent);color:#fff}}
.btn-online:hover{{background:var(--accent2);transform:translateY(-2px)}}
.btn-dl{{background:var(--bg3);color:var(--txt);border:1.5px solid var(--border)}}
.btn-dl:hover{{border-color:var(--accent);transform:translateY(-2px)}}
.btn-fav{{background:none;border:1.5px solid var(--border);color:var(--txt2);width:40px;flex:none;font-size:1.1rem;border-radius:10px}}
.btn-fav:hover{{border-color:var(--warn);color:var(--warn);transform:scale(1.1)}}
.btn-fav.is-fav{{color:var(--warn);border-color:var(--warn);animation:pulse .3s ease}}
.bottom-nav{{position:fixed;bottom:0;left:0;right:0;background:var(--bg2);border-top:1px solid var(--border);display:flex;justify-content:space-around;padding:.4rem 0 calc(.4rem + env(safe-area-inset-bottom));z-index:100;backdrop-filter:blur(20px);animation:fadeInUp .5s ease}}
.nitem{{background:none;border:none;color:var(--txt2);padding:.4rem .8rem;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:.15rem;font-size:.65rem;font-weight:600;transition:all .3s ease}}
.nitem:hover{{color:var(--accent);transform:translateY(-2px)}}
.nitem.active{{color:var(--accent)}}
.nicon{{font-size:1rem;font-weight:800}}
.toast{{position:fixed;bottom:85px;left:50%;transform:translateX(-50%) translateY(100px);background:var(--bg2);color:var(--txt);padding:.7rem 1.3rem;border-radius:25px;box-shadow:0 8px 30px rgba(0,0,0,.3);z-index:1000;opacity:0;transition:all .4s cubic-bezier(.4,0,.2,1);pointer-events:none;border:1px solid var(--border);font-size:.85rem;font-weight:600}}
.toast.show{{opacity:1;transform:translateX(-50%) translateY(0)}}
.empty{{text-align:center;padding:4rem 1rem;color:var(--txt2);animation:fadeInUp .5s ease}}
.empty-icon{{font-size:1.5rem;font-weight:800;margin-bottom:1rem;color:var(--accent2);animation:pulse 2s ease-in-out infinite}}
@media(min-width:768px){{body{{padding-bottom:0}}.bottom-nav{{display:none}}.main{{padding:0 2rem}}.grid{{grid-template-columns:repeat(auto-fill,minmax(240px,1fr))}}}}
@media(max-width:480px){{.grid{{grid-template-columns:repeat(2,1fr)}}}}
</style>
</head>
<body>
<div class="header">
  <div class="header-top">
    <div class="logo">StemPlay Library</div>
    <button class="theme-btn" id="themeBtn">Tema</button>
  </div>
  <div class="stats-row">
    <div class="chip"><b id="sT">0</b>materiais</div>
    <div class="chip"><b id="sC">0</b>cursos</div>
    <div class="chip"><b id="sV">0</b>visiveis</div>
  </div>
  <div class="search-wrap">
    <input type="text" class="search" id="searchBox" placeholder="Buscar curso, aula, modulo..." autocomplete="off">
  </div>
  <div class="filters" id="filterBar">
    <button class="fbtn active" data-t="all">Todos</button>
    <button class="fbtn" data-t="Standard">Padrao</button>
    <button class="fbtn" data-t="Teacher">Teacher</button>
    <button class="fbtn" data-t="Workbook">Workbook</button>
    <button class="fbtn" data-t="Student">Student</button>
  </div>
</div>
<div class="main" id="app"></div>
<div class="bottom-nav">
  <button class="nitem active" data-a="home"><span class="nicon">HOME</span>Inicio</button>
  <button class="nitem" data-a="courses"><span class="nicon">CURSOS</span>Cursos</button>
  <button class="nitem" data-a="fav"><span class="nicon">FAV</span>Favoritos</button>
  <button class="nitem" data-a="top"><span class="nicon">TOPO</span>Topo</button>
</div>
<div class="toast" id="toast"></div>
<script>
const D={courses_json};
let cF='all',cS='',cV='home';
let favs=JSON.parse(localStorage.getItem('sp_favs')||'[]');
const $=id=>document.getElementById(id);
const $$=(s,p)=>(p||document).querySelectorAll(s);

function hashString(s){{let h=0;for(let i=0;i<s.length;i++)h=((h<<5)-h)+s.charCodeAt(i);return Math.abs(h)}}
function courseGradient(course){{
  const h=hashString(course);
  const hue1=h%360;
  const hue2=(hue1+40)%360;
  const sat=65+(h%20);
  const lit=45+(h%15);
  return `linear-gradient(135deg, hsl(${{hue1}} ${{sat}}% ${{lit}}%) 0%, hsl(${{hue2}} ${{sat}}% ${{lit-10}}%) 100%)`;
}}

function toast(m){{const t=$('toast');t.textContent=m;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2200)}}

async function downloadPDF(url,name){{
  try{{
    toast('Baixando...');
    const r=await fetch(url);
    if(!r.ok)throw 0;
    const b=await r.blob();
    const a=document.createElement('a');
    a.href=URL.createObjectURL(b);
    a.download=name+'.pdf';
    document.body.appendChild(a);a.click();a.remove();
    toast('Download iniciado');
  }}catch(e){{
    window.open(url,'_blank');
    toast('Aberto em nova aba');
  }}
}}

function renderPlaceholder(course, type){{
  const letter = course.charAt(0).toUpperCase();
  const bg = courseGradient(course);
  return `<div class="thumb-wrap"><div class="placeholder" style="background:${{bg}}"><div class="ph-letter">${{letter}}</div><div class="ph-type">${{type}}</div><div class="ph-course">${{course}}</div></div></div>`;
}}

function render(){{
  const app=$('app');app.innerHTML='';let vc=0;const sl=cS.toLowerCase();
  let delay=0;
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
    ce.style.animationDelay=`${{delay*0.05}}s`;delay++;
    ce.innerHTML=`<div class="chdr"><div class="ctitle">${{c.name}}</div><div class="ccount">${{fi.length}}</div><div class="carrow">&#9660;</div></div><div class="cbody"></div>`;
    const cb=ce.querySelector('.cbody');
    Object.entries(gs).forEach(([gn,items])=>{{
      const gt=document.createElement('div');gt.className='gtitle';gt.textContent=gn+' · '+items.length+' itens';cb.appendChild(gt);
      const gr=document.createElement('div');gr.className='grid';
      items.forEach((i,idx)=>{{
        const a=document.createElement('div');a.className='card '+i.material_type.toLowerCase();
        a.style.animationDelay=`${{idx*0.03}}s`;
        const bc='b-'+i.material_type.toLowerCase();
        const isF=favs.includes(i.url);
        const onlineUrl='https://reader.stemplay.io/?file='+encodeURIComponent(i.url)+'&userId=k3s';
        let badges=`<span class="badge ${{bc}}">${{i.material_type}}</span>`;
        if(i.module_num)badges+=`<span class="badge" style="background:#8b5cf6;color:#fff">M${{i.module_num}}</span>`;
        if(i.unit_num)badges+=`<span class="badge" style="background:#ec4899;color:#fff">U${{i.unit_num}}</span>`;

        a.innerHTML=`${{renderPlaceholder(i.course, i.material_type)}}<div class="card-body"><div class="card-name">${{i.display_name}}</div><div class="card-badges">${{badges}}</div><div class="card-actions"><a href="${{onlineUrl}}" target="_blank" rel="noopener" class="abtn btn-online">Online</a><button class="abtn btn-dl">Download</button><button class="abtn btn-fav${{isF?' is-fav':''}}">${{isF?'&#9733;':'&#9734;'}}</button></div></div>`;

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
  if(!vc)app.innerHTML=`<div class="empty"><div class="empty-icon">${{cV==='fav'?'FAV':'BUSCA'}}</div><h3>${{cV==='fav'?'Nenhum favorito':'Nada encontrado'}}</h3><p style="margin-top:.5rem;font-size:.85rem;color:var(--txt2)">${{cV==='fav'?'Toque na estrela para favoritar':'Tente outra busca'}}</p></div>`;
}}

function toggleFav(u){{const i=favs.indexOf(u);if(i>=0){{favs.splice(i,1);toast('Removido')}}else{{favs.push(u);toast('Adicionado aos favoritos')}}localStorage.setItem('sp_favs',JSON.stringify(favs));render()}}

$('themeBtn').onclick=()=>{{const c=document.documentElement.getAttribute('data-theme');const n=c==='dark'?'light':'dark';document.documentElement.setAttribute('data-theme',n);localStorage.setItem('sp_theme',n);toast(n==='dark'?'Modo escuro':'Modo claro')}};

let st;
$('searchBox').oninput=e=>{{clearTimeout(st);st=setTimeout(()=>{{cS=e.target.value;render()}},180)}};

$('filterBar').onclick=e=>{{const b=e.target.closest('.fbtn');if(!b)return;$$('.fbtn').forEach(x=>x.classList.remove('active'));b.classList.add('active');cF=b.dataset.t;render()}};

$$('.nitem').forEach(b=>b.onclick=function(){{if(this.dataset.a==='top'){{window.scrollTo({{top:0,behavior:'smooth'}});return}}$$('.nitem').forEach(x=>x.classList.remove('active'));this.classList.add('active');cV=this.dataset.a;render()}});

document.documentElement.setAttribute('data-theme',localStorage.getItem('sp_theme')||'dark');
render();
</script>
</body>
</html>"""

    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  [OK] Biblioteca gerada: {output_html}")
    print(f"  [INFO] {len(courses)} cursos | {len(pdfs)} materiais")

if __name__ == "__main__":
    main()
