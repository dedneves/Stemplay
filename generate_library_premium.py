#!/usr/bin/env python3
"""
HAAAAAAAAAAA UMA EXPLOSAO DE HORROR 
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
    """Parse ultra-agressivo com limpeza completa de nomes"""
    filename = url.split("/")[-1].replace(".pdf", "")
    parts = url.split("/")
    
    # Extrai nome do curso (remove sufixos)
    course_raw = parts[4] if len(parts) > 4 else "OUTROS"
    course_clean = re.sub(r'[-_](TEACHER|STUDENT|WORKBOOK)$', '', course_raw, flags=re.IGNORECASE)
    course = course_clean.replace("-", " ").replace("_", " ").title()
    
    # Detecta tipo de material
    filename_upper = filename.upper()
    is_teacher = "TEACHER" in filename_upper or course_raw.upper().endswith("TEACHER")
    is_student = "STUDENT" in filename_upper or "STUDENT-BOOK" in filename_upper
    is_workbook = "WORKBOOK" in filename_upper or "WORK-BOOK" in filename_upper
    
    if is_teacher:
        material_type = "Teacher"
    elif is_workbook:
        material_type = "Workbook"
    elif is_student:
        material_type = "Student"
    else:
        material_type = "Standard"
    
    # Extrai numeros
    lesson_match = re.search(r'(?:Aula|Lesson|Class)(\d+)', filename, re.IGNORECASE)
    unit_match = re.search(r'Unit(\d+)', filename)
    module_match = re.search(r'M(\d+)', filename)
    checkpoint_match = re.search(r'Checkpoint(\d+)', filename, re.IGNORECASE)
    
    lesson_num = int(lesson_match.group(1)) if lesson_match else None
    unit_num = int(unit_match.group(1)) if unit_match else None
    module_num = int(module_match.group(1)) if module_match else None
    checkpoint_num = int(checkpoint_match.group(1)) if checkpoint_match else None
    
    # ==========================================
    # EXTRAÇÃO AGRESSIVA DO DISPLAY_NAME
    # ==========================================
    display_name = None
    
    # 1. Padrões com número (prioridade máxima)
    if lesson_num:
        display_name = f"Aula {lesson_num:02d}"
    elif unit_num:
        display_name = f"Unidade {unit_num:02d}"
    elif module_num:
        display_name = f"Modulo {module_num}"
    elif checkpoint_num:
        display_name = f"Checkpoint {checkpoint_num:02d}"
    else:
        # 2. Casos especiais conhecidos
        special_names = {
            'grammarreference': 'Grammar Reference',
            'checkpointkey': 'Checkpoint Key',
            'answerkey': 'Answer Key',
            'audioscript': 'Audio Script',
            'audioscripts': 'Audio Scripts',
            'extraresources': 'Extra Resources',
            'workbookanswerkey': 'Workbook Answer Key',
            'consolidationwbkey': 'Consolidation Workbook Key',
            'workbook': 'Workbook',
            'unit00': 'Unit 00',
        }
        
        filename_lower = filename.lower()
        for key, value in special_names.items():
            if key in filename_lower:
                display_name = value
                break
        
        # 3. Se não achou padrão especial, extrai o que sobra
        if not display_name:
            # Remove TUDO que é ruído
            name_clean = filename
            
            # Remove nome do curso no início
            name_clean = re.sub(r'^[A-Z0-9]+[-_]', '', name_clean)
            
            # Remove STUDENT BOOK / TEACHER BOOK / WORKBOOK
            name_clean = re.sub(r'[-_](STUDENT|TEACHER)[-_]?BOOK[-_]', ' ', name_clean, flags=re.IGNORECASE)
            name_clean = re.sub(r'[-_](STUDENT|TEACHER|WORKBOOK)[-_]', ' ', name_clean, flags=re.IGNORECASE)
            
            # Remove sufixos teacher/student/workbook
            name_clean = re.sub(r'[-_](teacher|student|workbook)$', '', name_clean, flags=re.IGNORECASE)
            
            # Remove Unit00, Unit01, etc se não tiver número capturado
            if not unit_num:
                name_clean = re.sub(r'Unit\d+', '', name_clean, flags=re.IGNORECASE)
            
            # Limpa espaços múltiplos e hífens
            name_clean = re.sub(r'[-_]+', ' ', name_clean)
            name_clean = re.sub(r'\s+', ' ', name_clean).strip()
            
            # Formata bonito
            display_name = name_clean.title() if name_clean else filename.replace("_", " ").replace("-", " ").title()
    
    # ==========================================
    # GRUPO E ORDENAÇÃO
    # ==========================================
    if checkpoint_num:
        sort_key = (0, 0, checkpoint_num)
        group_name = "Checkpoints"
    elif module_num and lesson_num:
        sort_key = (module_num, lesson_num, 0)
        group_name = f"Modulo {module_num}"
    elif unit_num:
        sort_key = (unit_num, 0, 0)
        group_name = "Unidades"
    else:
        sort_key = (0, 0, 0)
        group_name = "Geral"
    
    return {
        "url": url,
        "course": course,
        "course_raw": course_raw,
        "display_name": display_name,
        "material_type": material_type,
        "lesson_num": lesson_num,
        "unit_num": unit_num,
        "module_num": module_num,
        "checkpoint_num": checkpoint_num,
        "sort_key": sort_key,
        "group_name": group_name
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
    
    # Deduplicacao: remove URLs duplicadas mantendo a primeira
    urls_vistas = set()
    pdfs_unicos = []
    for pdf in pdfs:
        if pdf['url'] not in urls_vistas:
            urls_vistas.add(pdf['url'])
            pdfs_unicos.append(pdf)
    
    pdfs = pdfs_unicos
    print(f"  [INFO] Apos deduplicacao: {len(pdfs)} arquivos")
    
    # Agrupa por curso
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
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover,maximum-scale=5">
<meta name="theme-color" content="#0a0a1a">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<title>StemPlay Library</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}}

:root{{--bg:#0a0a1a;--bg2:#12122a;--bg3:#1a1a3e;--accent:#6c5ce7;--accent2:#a29bfe;--glow:rgba(108,92,231,.2);--txt:#f0f0ff;--txt2:#8888aa;--card:rgba(26,26,62,.7);--border:#2a2a5e;--ok:#00cec9;--warn:#fdcb6e;--radius:14px;--trans:.3s ease}}

html[data-theme="light"]{{--bg:#f4f6fb;--bg2:#ffffff;--bg3:#e8ecf5;--accent:#6c5ce7;--accent2:#5a4bd1;--glow:rgba(108,92,231,.1);--txt:#1a1a2e;--txt2:#666;--card:rgba(255,255,255,.9);--border:#dde1ea}}

body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--txt);min-height:100vh;min-height:100dvh;padding-bottom:calc(70px + env(safe-area-inset-bottom,0px));overflow-x:hidden;transition:background var(--trans),color var(--trans)}}

/* Header */
.header{{position:sticky;top:0;background:var(--bg2);border-bottom:1px solid var(--border);z-index:100;backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);transition:background var(--trans),border-color var(--trans)}}
.header-top{{display:flex;align-items:center;justify-content:space-between;padding:.875rem 1rem;gap:.75rem}}
.logo{{font-size:1.25rem;font-weight:900;background:linear-gradient(135deg,var(--accent),#fd79a8);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;letter-spacing:-.5px}}

/* Botao de tema com indicador visual */
.theme-btn{{position:relative;width:44px;height:44px;border-radius:50%;background:var(--bg3);border:1.5px solid var(--border);color:var(--txt);cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all var(--trans);font-size:1.2rem;touch-action:manipulation}}
.theme-btn:active{{transform:scale(.9)}}
.theme-btn::after{{content:'';position:absolute;inset:0;border-radius:50%;background:var(--accent);opacity:0;transform:scale(0);transition:all .4s ease}}
.theme-btn.animating::after{{opacity:.3;transform:scale(1.5);animation:ripple .6s ease-out}}
@keyframes ripple{{to{{opacity:0;transform:scale(2)}}}}

/* Stats */
.stats-row{{display:flex;gap:.5rem;padding:0 1rem .75rem;overflow-x:auto;scrollbar-width:none;-webkit-overflow-scrolling:touch}}
.stats-row::-webkit-scrollbar{{display:none}}
.chip{{background:var(--bg3);padding:.4rem .85rem;border-radius:20px;font-size:.75rem;white-space:nowrap;border:1px solid var(--border);flex-shrink:0;transition:all var(--trans);font-weight:600}}
.chip b{{color:var(--accent2);margin-right:.25rem;font-weight:800}}

/* Busca */
.search-wrap{{padding:0 1rem .75rem}}
.search{{width:100%;padding:.875rem 1rem;background:var(--bg3);border:2px solid var(--border);border-radius:var(--radius);color:var(--txt);font-size:1rem;transition:all var(--trans);touch-action:manipulation;-webkit-appearance:none}}
.search:focus{{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px var(--glow)}}
.search::placeholder{{color:var(--txt2)}}

/* Filtros */
.filters{{display:flex;gap:.5rem;padding:0 1rem 1rem;overflow-x:auto;scrollbar-width:none;-webkit-overflow-scrolling:touch}}
.filters::-webkit-scrollbar{{display:none}}
.fbtn{{padding:.5rem 1rem;background:var(--bg3);border:1.5px solid var(--border);border-radius:20px;color:var(--txt2);cursor:pointer;font-weight:600;font-size:.8rem;white-space:nowrap;transition:all var(--trans);flex-shrink:0;touch-action:manipulation}}
.fbtn.active{{background:var(--accent);border-color:var(--accent);color:#fff}}
.fbtn:active{{transform:scale(.95)}}

/* Conteudo */
.main{{padding:0 .75rem;max-width:1400px;margin:0 auto}}
.course{{background:var(--bg2);border-radius:var(--radius);margin-bottom:.75rem;border:1px solid var(--border);overflow:hidden;transition:all var(--trans)}}
.chdr{{padding:.875rem 1rem;cursor:pointer;display:flex;justify-content:space-between;align-items:center;user-select:none;-webkit-user-select:none;transition:background var(--trans);min-height:52px;touch-action:manipulation}}
.chdr:active{{background:var(--bg3)}}
.ctitle{{font-size:.95rem;font-weight:700;flex:1;margin-right:.5rem;line-height:1.35}}
.ccount{{background:var(--accent);color:#fff;padding:.2rem .6rem;border-radius:10px;font-size:.7rem;font-weight:800;flex-shrink:0}}
.carrow{{color:var(--txt2);transition:transform .3s ease;font-size:.9rem;margin-left:.5rem;flex-shrink:0}}
.course.open .carrow{{transform:rotate(180deg)}}
.cbody{{display:none;padding:0 1rem 1rem}}
.course.open .cbody{{display:block;animation:fadeIn .25s ease}}
@keyframes fadeIn{{from{{opacity:0}}to{{opacity:1}}}}

/* Grupo */
.gtitle{{color:var(--accent2);font-size:.75rem;font-weight:700;margin:.75rem 0 .5rem;text-transform:uppercase;letter-spacing:.5px}}

/* Grid otimizado */
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:.6rem}}
@media(max-width:480px){{.grid{{grid-template-columns:1fr}}}}
@media(min-width:768px){{.grid{{grid-template-columns:repeat(auto-fill,minmax(240px,1fr))}}}}

/* Cards */
.card{{background:var(--card);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);border-radius:var(--radius);color:var(--txt);border:1.5px solid var(--border);display:flex;flex-direction:column;overflow:hidden;transition:transform .15s ease,border-color .2s ease,box-shadow .2s ease,background var(--trans);content-visibility:auto;contain-intrinsic-size:auto 300px}}
.card:active{{transform:scale(.98)}}

/* Placeholder melhorado */
.thumb-wrap{{position:relative;width:100%;aspect-ratio:4/3;background:var(--bg3);overflow:hidden;border-bottom:1px solid var(--border)}}
.placeholder{{width:100%;height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:.5rem;position:relative;overflow:hidden;transition:transform .3s ease}}
.placeholder::before{{content:'';position:absolute;inset:0;opacity:.12;background:radial-gradient(circle at 30% 20%,rgba(255,255,255,.5),transparent 50%)}}
.ph-letter{{font-size:3.5rem;font-weight:900;color:rgba(255,255,255,.95);text-shadow:0 2px 15px rgba(0,0,0,.3);letter-spacing:-2px;z-index:1;line-height:1}}
.ph-type{{font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:2px;color:rgba(255,255,255,.9);padding:.2rem .5rem;border-radius:8px;background:rgba(0,0,0,.2);backdrop-filter:blur(8px);z-index:1}}
.ph-course{{position:absolute;bottom:.4rem;left:.4rem;right:.4rem;font-size:.6rem;color:rgba(255,255,255,.85);font-weight:600;text-align:center;z-index:1;text-shadow:0 1px 2px rgba(0,0,0,.5);line-height:1.2;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}

/* Corpo do card */
.card-body{{padding:.75rem .875rem;display:flex;flex-direction:column;gap:.4rem;flex:1}}
.card-name{{font-weight:700;font-size:.9rem;line-height:1.3;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.card-badges{{display:flex;gap:.25rem;flex-wrap:wrap}}
.badge{{padding:.15rem .5rem;border-radius:8px;font-size:.6rem;font-weight:800;text-transform:uppercase;letter-spacing:.3px;transition:all var(--trans)}}
.b-teacher{{background:var(--warn);color:#1a1a2e}}
.b-workbook{{background:var(--ok);color:#1a1a2e}}
.b-student,.b-standard{{background:var(--accent);color:#fff}}

/* Acoes */
.card-actions{{display:flex;gap:.35rem;margin-top:auto;padding-top:.4rem}}
.abtn{{flex:1;padding:.6rem;border:none;border-radius:10px;font-size:.75rem;font-weight:700;cursor:pointer;text-align:center;text-decoration:none;display:flex;align-items:center;justify-content:center;gap:.3rem;transition:all .15s ease;color:inherit;touch-action:manipulation;min-height:44px}}
.abtn:active{{transform:scale(.95)}}
.btn-online{{background:var(--accent);color:#fff}}
.btn-dl{{background:var(--bg3);color:var(--txt);border:1.5px solid var(--border)}}
.btn-fav{{background:none;border:1.5px solid var(--border);color:var(--txt2);width:44px;flex:none;font-size:1.1rem;border-radius:10px;padding:0}}
.btn-fav.is-fav{{color:var(--warn);border-color:var(--warn)}}

/* Bottom nav */
.bottom-nav{{position:fixed;bottom:0;left:0;right:0;background:var(--bg2);border-top:1px solid var(--border);display:flex;justify-content:space-around;padding:.5rem 0 calc(.5rem + env(safe-area-inset-bottom,0px));z-index:100;backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);transition:background var(--trans),border-color var(--trans)}}
.nitem{{background:none;border:none;color:var(--txt2);padding:.5rem .75rem;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:.2rem;font-size:.65rem;font-weight:600;transition:color var(--trans);touch-action:manipulation;min-width:60px}}
.nitem.active{{color:var(--accent)}}
.nitem:active{{opacity:.7}}
.nicon{{font-size:.9rem;font-weight:800;letter-spacing:-.5px}}

/* Toast */
.toast{{position:fixed;bottom:calc(80px + env(safe-area-inset-bottom,0px));left:50%;transform:translateX(-50%) translateY(100px);background:var(--bg2);color:var(--txt);padding:.7rem 1.25rem;border-radius:25px;box-shadow:0 8px 25px rgba(0,0,0,.25);z-index:1000;opacity:0;transition:all .3s cubic-bezier(.4,0,.2,1);pointer-events:none;border:1px solid var(--border);font-size:.85rem;font-weight:600;white-space:nowrap}}
.toast.show{{opacity:1;transform:translateX(-50%) translateY(0)}}

/* Empty */
.empty{{text-align:center;padding:3rem 1rem;color:var(--txt2)}}
.empty-icon{{font-size:1.5rem;font-weight:800;margin-bottom:1rem;color:var(--accent2)}}

/* Desktop */
@media(min-width:768px){{
  body{{padding-bottom:0}}
  .bottom-nav{{display:none}}
  .main{{padding:0 2rem}}
  .header-top,.search-wrap,.filters,.stats-row{{padding-left:2rem;padding-right:2rem}}
  .card:hover{{transform:translateY(-2px);border-color:var(--accent);box-shadow:0 6px 20px var(--glow)}}
}}

/* Transicao global de tema */
html.theme-transitioning,
html.theme-transitioning *,
html.theme-transitioning *::before,
html.theme-transitioning *::after{{transition:background-color .4s ease,color .4s ease,border-color .4s ease,box-shadow .4s ease !important}}
</style>
</head>
<body>
<div class="header">
  <div class="header-top">
    <div class="logo">StemPlay Library</div>
    <button class="theme-btn" id="themeBtn" aria-label="Alternar tema">&#9790;</button>
  </div>
  <div class="stats-row">
    <div class="chip"><b id="sT">0</b>materiais</div>
    <div class="chip"><b id="sC">0</b>cursos</div>
    <div class="chip"><b id="sV">0</b>visiveis</div>
  </div>
  <div class="search-wrap">
    <input type="text" class="search" id="searchBox" placeholder="Buscar curso, aula, modulo..." autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false">
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
let favs=new Set(JSON.parse(localStorage.getItem('sp_favs')||'[]'));
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

let toastTimer;
function toast(m){{
  const t=$('toast');
  t.textContent=m;
  t.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer=setTimeout(()=>t.classList.remove('show'),2200);
}}

async function downloadPDF(url,name){{
  try{{
    toast('Iniciando download...');
    const r=await fetch(url);
    if(!r.ok)throw 0;
    const b=await r.blob();
    const a=document.createElement('a');
    a.href=URL.createObjectURL(b);
    a.download=name+'.pdf';
    document.body.appendChild(a);
    a.click();
    setTimeout(()=>{{a.remove();URL.revokeObjectURL(a.href)}},100);
    toast('Download iniciado');
  }}catch(e){{
    window.open(url,'_blank');
    toast('Aberto em nova aba');
  }}
}}

function renderPlaceholder(course, type){{
  const letter=course.charAt(0).toUpperCase();
  const bg=courseGradient(course);
  return `<div class="thumb-wrap"><div class="placeholder" style="background:${{bg}}"><div class="ph-letter">${{letter}}</div><div class="ph-type">${{type}}</div><div class="ph-course">${{course}}</div></div></div>`;
}}

function render(){{
  const app=$('app');
  app.innerHTML='';
  let vc=0;
  const sl=cS.toLowerCase();
  
  D.forEach(c=>{{
    const fi=c.items.filter(i=>{{
      const ms=!sl||i.course.toLowerCase().includes(sl)||i.display_name.toLowerCase().includes(sl)||i.group_name.toLowerCase().includes(sl);
      const mf=cF==='all'||i.material_type===cF;
      if(cV==='fav')return favs.has(i.url);
      return ms&&mf;
    }});
    if(!fi.length)return;
    vc+=fi.length;
    
    const gs={{}};
    fi.forEach(i=>{{(gs[i.group_name]=gs[i.group_name]||[]).push(i)}});
    
    const ce=document.createElement('div');
    ce.className='course';
    ce.innerHTML=`<div class="chdr"><div class="ctitle">${{c.name}}</div><div class="ccount">${{fi.length}}</div><div class="carrow">&#9660;</div></div><div class="cbody"></div>`;
    
    const cb=ce.querySelector('.cbody');
    Object.entries(gs).forEach(([gn,items])=>{{
      const gt=document.createElement('div');
      gt.className='gtitle';
      gt.textContent=gn+' · '+items.length+' itens';
      cb.appendChild(gt);
      
      const gr=document.createElement('div');
      gr.className='grid';
      items.forEach(i=>{{
        const a=document.createElement('div');
        a.className='card '+i.material_type.toLowerCase();
        const bc='b-'+i.material_type.toLowerCase();
        const isF=favs.has(i.url);
        const onlineUrl='https://reader.stemplay.io/?file='+encodeURIComponent(i.url)+'&userId=k3s';
        
        let badges=`<span class="badge ${{bc}}">${{i.material_type}}</span>`;
        if(i.module_num)badges+=`<span class="badge" style="background:#8b5cf6;color:#fff">M${{i.module_num}}</span>`;
        if(i.unit_num)badges+=`<span class="badge" style="background:#ec4899;color:#fff">U${{i.unit_num}}</span>`;
        
        a.innerHTML=`${{renderPlaceholder(i.course,i.material_type)}}<div class="card-body"><div class="card-name">${{i.display_name}}</div><div class="card-badges">${{badges}}</div><div class="card-actions"><a href="${{onlineUrl}}" target="_blank" rel="noopener" class="abtn btn-online">Online</a><button class="abtn btn-dl">Download</button><button class="abtn btn-fav${{isF?' is-fav':''}}">${{isF?'&#9733;':'&#9734;'}}</button></div></div>`;
        
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
  $('sC').textContent=D.length;
  $('sV').textContent=vc;
  
  if(!vc){{
    app.innerHTML=`<div class="empty"><div class="empty-icon">${{cV==='fav'?'FAV':'BUSCA'}}</div><h3>${{cV==='fav'?'Nenhum favorito':'Nada encontrado'}}</h3><p style="margin-top:.5rem;font-size:.85rem;color:var(--txt2)">${{cV==='fav'?'Toque na estrela para favoritar':'Tente outra busca'}}</p></div>`;
  }}
}}

function toggleFav(u){{
  if(favs.has(u)){{
    favs.delete(u);
    toast('Removido dos favoritos');
  }}else{{
    favs.add(u);
    toast('Adicionado aos favoritos');
  }}
  localStorage.setItem('sp_favs',JSON.stringify([...favs]));
  render();
}}

// Tema com transicao suave
function toggleTheme(){{
  const html=document.documentElement;
  const btn=$('themeBtn');
  
  // Adiciona classe de transicao
  html.classList.add('theme-transitioning');
  
  // Troca tema
  const current=html.getAttribute('data-theme');
  const next=current==='dark'?'light':'dark';
  html.setAttribute('data-theme',next);
  localStorage.setItem('sp_theme',next);
  
  // Atualiza icone
  btn.innerHTML=next==='dark'?'&#9790;':'&#9728;';
  
  // Efeito ripple no botao
  btn.classList.add('animating');
  setTimeout(()=>btn.classList.remove('animating'),600);
  
  toast(next==='dark'?'Modo escuro':'Modo claro');
  
  // Remove classe de transicao
  setTimeout(()=>html.classList.remove('theme-transitioning'),400);
}}

$('themeBtn').onclick=toggleTheme;

// Busca com debounce
let searchTimer;
$('searchBox').oninput=e=>{{
  clearTimeout(searchTimer);
  searchTimer=setTimeout(()=>{{cS=e.target.value;render()}},200);
}};

// Filtros
$('filterBar').onclick=e=>{{
  const b=e.target.closest('.fbtn');
  if(!b)return;
  $$('.fbtn').forEach(x=>x.classList.remove('active'));
  b.classList.add('active');
  cF=b.dataset.t;
  render();
}};

// Nav
$$('.nitem').forEach(b=>b.onclick=function(){{
  if(this.dataset.a==='top'){{
    window.scrollTo({{top:0,behavior:'smooth'}});
    return;
  }}
  $$('.nitem').forEach(x=>x.classList.remove('active'));
  this.classList.add('active');
  cV=this.dataset.a;
  render();
}});

// Init
const savedTheme=localStorage.getItem('sp_theme')||'dark';
document.documentElement.setAttribute('data-theme',savedTheme);
$('themeBtn').innerHTML=savedTheme==='dark'?'&#9790;':'&#9728;';
render();

console.log('StemPlay Library v8 |',D.reduce((s,c)=>s+c.items.length,0),'materiais em',D.length,'cursos');
</script>
</body>
</html>"""
    
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"  [OK] Biblioteca gerada: {output_html}")
    print(f"  [INFO] {len(courses)} cursos | {len(pdfs)} materiais (sem duplicatas)")

if __name__ == "__main__":
    main()
