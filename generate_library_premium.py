#!/usr/bin/env python3
"""
meu deus
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
    """Parse v12.1 - corrige Student/Teacher/Workbook e Capitulo/Unidade, sem mudar visual"""
    filename = url.split("/")[-1].replace(".pdf", "")
    parts = url.split("/")
    course_raw = parts[4] if len(parts) > 4 else "OUTROS"
    course_clean = re.sub(r'[-_](TEACHER|STUDENT|WORKBOOK)$', '', course_raw, flags=re.IGNORECASE)
    # Title case mas preserva siglas curtas legiveis
    course = course_clean.replace("-", " ").replace("_", " ").title()

    fn_up = filename.upper()
    url_up = url.upper()
    # Tokens para classificacao estrita (evita substring falso)
    tokens = re.split(r'[-_\s\.]+', fn_up)
    has_workbook = "WORKBOOK" in tokens or "WORKBOOK" in fn_up
    has_student_book = "STUDENT" in fn_up and "BOOK" in fn_up
    has_teacher = "TEACHER" in tokens or fn_up.endswith("_TEACHER") or fn_up.endswith("-TEACHER") or fn_up.endswith("_TEACHER")
    has_student = "STUDENT" in tokens
    path_is_teacher = "/TEACHER/" in url_up and "/STUDENT/" not in url_up
    path_is_student = "/STUDENT/" in url_up
    path_is_workbook = "/WORKBOOK/" in url_up

    # Prioridade corrigida: Workbook > Student-Book > Student > Teacher
    # Resolve 138 casos de STUDENT-BOOK_..._teacher que iam para Teacher indevidamente
    if has_workbook:
        material_type = "Workbook"
    elif has_student_book:
        material_type = "Student"
    elif has_student and has_teacher:
        material_type = "Student"
    elif has_student:
        material_type = "Student"
    elif has_teacher:
        material_type = "Teacher"
    elif path_is_workbook:
        material_type = "Workbook"
    elif path_is_student:
        material_type = "Student"
    elif path_is_teacher:
        material_type = "Teacher"
    else:
        material_type = "Standard"

    # --- Extracao de numeros com suporte a Capitulo/Unidade ---
    lesson_m = re.search(r'(?:Aula|Lesson|Class)\s*0*(\d+)', filename, re.IGNORECASE)
    # Unit: Unit, Unidade, Und, U
    unit_m = re.search(r'(?:Unit|Unidade|Und)\s*0*(\d+)', filename, re.IGNORECASE)
    if not unit_m:
        # Fallback _U1_ / -U2-
        unit_m = re.search(r'[_-]U0*(\d+)[_-]', filename, re.IGNORECASE)
    module_m = re.search(r'(?:Modulo|_M|[-_]M)0*(\d+)', filename, re.IGNORECASE)
    checkpoint_m = re.search(r'Checkpoint\s*0*(\d+)', filename, re.IGNORECASE)
    capitulo_m = re.search(r'Capitulo\s*0*(\d+)', filename, re.IGNORECASE)

    lesson_num = int(lesson_m.group(1)) if lesson_m else None
    unit_num = int(unit_m.group(1)) if unit_m else None
    module_num = int(module_m.group(1)) if module_m else None
    checkpoint_num = int(checkpoint_m.group(1)) if checkpoint_m else None
    capitulo_num = int(capitulo_m.group(1)) if capitulo_m else None

    display_name = None
    if lesson_num is not None:
        display_name = f"Aula {lesson_num:02d}"
    elif checkpoint_num is not None:
        display_name = f"Checkpoint {checkpoint_num:02d}"
    elif capitulo_num is not None:
        display_name = f"Capítulo {capitulo_num:02d}"
    elif unit_num is not None:
        display_name = f"Unidade {unit_num:02d}"
    elif module_num is not None:
        display_name = f"Modulo {module_num}"

    if not display_name:
        keywords = [
            (r'Grammar\s*Reference', 'Grammar Reference'),
            (r'Checkpoint\s*Key', 'Checkpoint Key'),
            (r'Answer\s*Key', 'Answer Key'),
            (r'Audio\s*Scripts?', 'Audio Script'),
            (r'Extra\s*Resources?', 'Extra Resources'),
            (r'Workbook\s*Answer\s*Key', 'Workbook Answer Key'),
            (r'Consolidation.*Key', 'Consolidation Key'),
            (r'Workbook(?!Answer)', 'Workbook'),
            (r'Unit\s*00', 'Unit 00'),
            (r'Teacher\s*Book', 'Teacher Book'),
            (r'Student\s*Book', 'Student Book'),
            (r'Song\s*Book', 'Song Book'),
        ]
        for pattern, name in keywords:
            if re.search(pattern, filename, re.IGNORECASE):
                display_name = name
                break

    if not display_name:
        segments = re.split(r'[-_]', filename)
        useless = {'ENGLISH', 'TEEN1', 'TEEN2', 'TEEN3', 'JUNIOR', 'PLENO',
                   'STUDENT', 'TEACHER', 'BOOK', 'WORKBOOK', 'COM', 'DE',
                   'AO', 'LV1', 'LV2', 'I', 'II', 'III', 'INICIANTE', 'CB', 'HAPPY', 'KIDS', 'SONG'}
        meaningful = [s for s in segments if s.upper() not in useless and len(s) > 2 and not s.isdigit()]
        if meaningful:
            display_name = " ".join(meaningful[-2:]).title() if len(meaningful) > 1 else meaningful[0].title()
        else:
            display_name = filename.replace("_", " ").replace("-", " ").title()

    # Agrupamento e ordenacao - Geral por ultimo (999) para nao misturar com Aulas
    if checkpoint_num is not None:
        sort_key = (0, 0, checkpoint_num)
        group_name = "Checkpoints"
    elif capitulo_num is not None:
        # Capitulo dentro de Unidade quando houver
        sort_key = (unit_num or 0, capitulo_num, 0)
        group_name = f"Unidade {unit_num:02d}" if unit_num is not None else "Capítulos"
    elif module_num is not None and lesson_num is not None:
        sort_key = (module_num, lesson_num, 0)
        group_name = f"Modulo {module_num}"
    elif module_num is not None:
        sort_key = (module_num, 0, 0)
        group_name = f"Modulo {module_num}"
    elif unit_num is not None:
        sort_key = (unit_num, 0, 0)
        group_name = "Unidades"
    else:
        sort_key = (999, 0, 0)
        group_name = "Geral"

    return {
        "url": url, "course": course, "course_raw": course_raw,
        "display_name": display_name, "material_type": material_type,
        "lesson_num": lesson_num, "unit_num": unit_num, "module_num": module_num,
        "checkpoint_num": checkpoint_num, "capitulo_num": capitulo_num, "sort_key": sort_key, "group_name": group_name
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

    # Deduplicacao por URL
    urls_vistas = set()
    pdfs_unicos = []
    for pdf in pdfs:
        if pdf['url'] not in urls_vistas:
            urls_vistas.add(pdf['url'])
            pdfs_unicos.append(pdf)
    pdfs = pdfs_unicos

    # Deduplicacao por conteudo
    vistos = {}
    pdfs_dedup = []
    for pdf in pdfs:
        chave = (pdf['course'].lower(), pdf['display_name'].lower(),
                 pdf['material_type'].lower(), pdf['group_name'].lower())
        if chave not in vistos:
            vistos[chave] = True
            pdfs_dedup.append(pdf)
    print(f"  [INFO] Deduplicacao: {len(pdfs_unicos)} -> {len(pdfs_dedup)} arquivos")
    pdfs = pdfs_dedup

    courses_dict = defaultdict(list)
    for pdf in pdfs:
        courses_dict[pdf['course']].append(pdf)

    courses = [{"name": n, "items": sorted(it, key=lambda x: x['sort_key'])}
               for n, it in sorted(courses_dict.items())]

    courses_json = json.dumps(courses, ensure_ascii=False)
    print("  [INFO] Gerando biblioteca HTML...")

    html_template = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover,maximum-scale=5">
<meta name="theme-color" content="#0a0a1a">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<title>StemPlay Library</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
:root{--bg:#0a0a1a;--bg2:#12122a;--bg3:#1a1a3e;--accent:#6c5ce7;--accent2:#a29bfe;--glow:rgba(108,92,231,.2);--txt:#f0f0ff;--txt2:#8888aa;--card:rgba(26,26,62,.7);--border:#2a2a5e;--ok:#00cec9;--warn:#fdcb6e;--radius:14px;--trans:.3s ease;--ease-out-expo:cubic-bezier(.16,1,.3,1)}
html[data-theme="light"]{--bg:#f4f6fb;--bg2:#ffffff;--bg3:#e8ecf5;--accent:#6c5ce7;--accent2:#5a4bd1;--glow:rgba(108,92,231,.1);--txt:#1a1a2e;--txt2:#666;--card:rgba(255,255,255,.9);--border:#dde1ea}
html{scroll-behavior:smooth}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--txt);min-height:100vh;min-height:100dvh;padding-bottom:calc(70px + env(safe-area-inset-bottom,0px));overflow-x:hidden;transition:background var(--trans),color var(--trans)}
.header{position:sticky;top:0;background:var(--bg2);border-bottom:1px solid var(--border);z-index:100;transition:background var(--trans),border-color var(--trans)}
.header-top{display:flex;align-items:center;justify-content:space-between;padding:.875rem 1rem;gap:.75rem}
.logo{font-size:1.25rem;font-weight:900;background:linear-gradient(135deg,var(--accent),#fd79a8);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;letter-spacing:-.5px}
.theme-btn{position:relative;width:44px;height:44px;border-radius:50%;background:var(--bg3);border:1.5px solid var(--border);color:var(--txt);cursor:pointer;display:flex;align-items:center;justify-content:center;transition:background var(--trans);font-size:1.2rem;touch-action:manipulation}
.theme-btn:active{transform:scale(.9)}
.theme-btn::after{content:'';position:absolute;inset:0;border-radius:50%;background:var(--accent);opacity:0;transform:scale(0);transition:all .4s ease}
.theme-btn.animating::after{opacity:.3;transform:scale(1.5);animation:ripple .6s ease-out}
@keyframes ripple{to{opacity:0;transform:scale(2)}}
.stats-row{display:flex;gap:.5rem;padding:0 1rem .75rem;overflow-x:auto;scrollbar-width:none;-webkit-overflow-scrolling:touch}
.stats-row::-webkit-scrollbar{display:none}
.chip{background:var(--bg3);padding:.4rem .85rem;border-radius:20px;font-size:.75rem;white-space:nowrap;border:1px solid var(--border);flex-shrink:0;transition:transform .2s var(--ease-out-expo),background var(--trans);font-weight:600}
.chip b{color:var(--accent2);margin-right:.25rem;font-weight:800}
.search-wrap{padding:0 1rem .75rem}
.search{width:100%;padding:.875rem 1rem;background:var(--bg3);border:2px solid var(--border);border-radius:var(--radius);color:var(--txt);font-size:1rem;transition:border-color .2s,box-shadow .2s;touch-action:manipulation;-webkit-appearance:none}
.search:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px var(--glow)}
.search::placeholder{color:var(--txt2)}
.filters{display:flex;gap:.5rem;padding:0 1rem 1rem;overflow-x:auto;scrollbar-width:none;-webkit-overflow-scrolling:touch}
.filters::-webkit-scrollbar{display:none}
.fbtn{padding:.5rem 1rem;background:var(--bg3);border:1.5px solid var(--border);border-radius:20px;color:var(--txt2);cursor:pointer;font-weight:600;font-size:.8rem;white-space:nowrap;transition:background .2s,border-color .2s,color .2s;flex-shrink:0;touch-action:manipulation}
.fbtn.active{background:var(--accent);border-color:var(--accent);color:#fff}
.fbtn:active{transform:scale(.95)}
.main{padding:0 .75rem;max-width:1400px;margin:0 auto}
.course{background:var(--bg2);border-radius:var(--radius);margin-bottom:.75rem;border:1px solid var(--border);overflow:hidden;transition:box-shadow .2s}
.chdr{padding:.875rem 1rem;cursor:pointer;display:flex;justify-content:space-between;align-items:center;user-select:none;-webkit-user-select:none;transition:background var(--trans);min-height:52px;touch-action:manipulation}
.chdr:active{background:var(--bg3)}
.ctitle{font-size:.95rem;font-weight:700;flex:1;margin-right:.5rem;line-height:1.35}
.ccount{background:var(--accent);color:#fff;padding:.2rem .6rem;border-radius:10px;font-size:.7rem;font-weight:800;flex-shrink:0}
.carrow{color:var(--txt2);transition:transform .3s var(--ease-out-expo);font-size:.9rem;margin-left:.5rem;flex-shrink:0}
.course.open .carrow{transform:rotate(180deg)}
.cbody{display:none;padding:0 1rem 1rem}
.course.open .cbody{display:block}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
.gtitle{color:var(--accent2);font-size:.75rem;font-weight:700;margin:.75rem 0 .5rem;text-transform:uppercase;letter-spacing:.5px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:.6rem}
@media(max-width:480px){.grid{grid-template-columns:1fr}}
@media(min-width:768px){.grid{grid-template-columns:repeat(auto-fill,minmax(240px,1fr))}}
.card{background:var(--card);border-radius:var(--radius);color:var(--txt);border:1.5px solid var(--border);display:flex;flex-direction:column;overflow:hidden;transition:transform .15s ease,border-color .15s,box-shadow .15s;background var(--trans);content-visibility:auto;contain-intrinsic-size:auto 300px}
.card:active{transform:scale(.98)}
@media(min-width:768px){.card:hover{transform:translateY(-3px);border-color:var(--accent);box-shadow:0 8px 24px var(--glow)}}
.thumb-wrap{position:relative;width:100%;aspect-ratio:4/3;background:var(--bg3);overflow:hidden;border-bottom:1px solid var(--border)}
.placeholder{width:100%;height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:.5rem;position:relative;overflow:hidden;transition:transform .3s var(--ease-out-expo)}
.placeholder::before{content:'';position:absolute;inset:0;opacity:.12;background:radial-gradient(circle at 30% 20%,rgba(255,255,255,.5),transparent 50%)}
.ph-letter{font-size:3.5rem;font-weight:900;color:rgba(255,255,255,.95);text-shadow:0 2px 15px rgba(0,0,0,.3);letter-spacing:-2px;z-index:1;line-height:1}
.ph-type{font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:2px;color:rgba(255,255,255,.9);padding:.2rem .5rem;border-radius:8px;background:rgba(0,0,0,.2);backdrop-filter:blur(8px);z-index:1}
.ph-course{position:absolute;bottom:.4rem;left:.4rem;right:.4rem;font-size:.6rem;color:rgba(255,255,255,.85);font-weight:600;text-align:center;z-index:1;text-shadow:0 1px 2px rgba(0,0,0,.5);line-height:1.2;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.thumb-canvas{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:none;background:var(--bg3)}
.thumb-wrap.has-thumb .thumb-canvas{display:block}
.thumb-wrap.has-thumb .placeholder{display:none}
.thumb-wrap.loading::after{content:'';position:absolute;inset:0;background:linear-gradient(90deg,transparent,rgba(255,255,255,.08),transparent);animation:shimmer 1.5s infinite}
@keyframes shimmer{0%{transform:translateX(-100%)}100%{transform:translateX(100%)}}
.card-body{padding:.75rem .875rem;display:flex;flex-direction:column;gap:.4rem;flex:1}
.card-name{font-weight:700;font-size:.9rem;line-height:1.3;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.card-badges{display:flex;gap:.25rem;flex-wrap:wrap}
.badge{padding:.15rem .5rem;border-radius:8px;font-size:.6rem;font-weight:800;text-transform:uppercase;letter-spacing:.3px;transition:all var(--trans)}
.b-teacher{background:var(--warn);color:#1a1a2e}
.b-workbook{background:var(--ok);color:#1a1a2e}
.b-student,.b-standard{background:var(--accent);color:#fff}
.card-actions{display:flex;gap:.35rem;margin-top:auto;padding-top:.4rem}
.abtn{flex:1;padding:.6rem;border:none;border-radius:10px;font-size:.75rem;font-weight:700;cursor:pointer;text-align:center;text-decoration:none;display:flex;align-items:center;justify-content:center;gap:.3rem;transition:transform .15s var(--ease-out-expo),background .15s,box-shadow .15s;color:inherit;touch-action:manipulation;min-height:44px}
.abtn:hover{transform:translateY(-1px)}
.abtn:active{transform:scale(.96)}
.btn-online{background:var(--accent);color:#fff}
.btn-dl{background:var(--bg3);color:var(--txt);border:1.5px solid var(--border)}
.btn-fav{background:none;border:1.5px solid var(--border);color:var(--txt2);width:44px;flex:none;font-size:1.1rem;border-radius:10px;padding:0;transition:transform .2s var(--ease-out-expo),color .2s,border-color .2s}
.btn-fav:hover{transform:scale(1.05)}
.btn-fav.is-fav{color:var(--warn);border-color:var(--warn)}
.bottom-nav{position:fixed;bottom:0;left:0;right:0;background:var(--bg2);border-top:1px solid var(--border);display:flex;justify-content:space-around;padding:.5rem 0 calc(.5rem + env(safe-area-inset-bottom,0px));z-index:100;transition:background var(--trans),border-color var(--trans)}
.nitem{background:none;border:none;color:var(--txt2);padding:.5rem .75rem;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:.2rem;font-size:.65rem;font-weight:600;transition:color .2s;touch-action:manipulation;min-width:60px}
.nitem.active{color:var(--accent)}
.nitem:active{opacity:.7;transform:scale(.9)}
.nicon{font-size:.9rem;font-weight:800;letter-spacing:-.5px}
.toast{position:fixed;bottom:calc(80px + env(safe-area-inset-bottom,0px));left:50%;transform:translateX(-50%) translateY(100px);background:var(--bg2);color:var(--txt);padding:.7rem 1.25rem;border-radius:25px;box-shadow:0 8px 25px rgba(0,0,0,.25);z-index:1000;opacity:0;transition:all .35s var(--ease-out-expo);pointer-events:none;border:1px solid var(--border);font-size:.85rem;font-weight:600;white-space:nowrap}
.toast.show{opacity:1;transform:translateX(-50%) translateY(0)}
.empty{text-align:center;padding:3rem 1rem;color:var(--txt2);animation:fadeIn .4s ease}
.empty-icon{font-size:1.5rem;font-weight:800;margin-bottom:1rem;color:var(--accent2)}
@media(min-width:768px){body{padding-bottom:0}.bottom-nav{display:none}.main{padding:0 2rem}.header-top,.search-wrap,.filters,.stats-row{padding-left:2rem;padding-right:2rem}.card:hover{transform:translateY(-2px);border-color:var(--accent);box-shadow:0 6px 20px var(--glow)}}
/* GATE ID - tela inicial obrigatoria */
#idGate{position:fixed;inset:0;z-index:9999;background:var(--bg);display:flex;align-items:center;justify-content:center;padding:1.5rem;transition:opacity .4s var(--ease-out-expo),visibility .4s}
#idGate.hidden{opacity:0;visibility:hidden;pointer-events:none}
.gate-card{background:var(--bg2);border:1.5px solid var(--border);border-radius:20px;padding:2rem 1.5rem;max-width:380px;width:100%;text-align:center;box-shadow:0 20px 60px rgba(0,0,0,.4)}
.gate-logo{font-size:1.8rem;font-weight:900;background:linear-gradient(135deg,var(--accent),#fd79a8);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:.25rem}
.gate-sub{color:var(--txt2);font-size:.9rem;margin-bottom:1.25rem;font-weight:600}
.gate-input{width:100%;padding:.9rem 1rem;background:var(--bg3);border:2px solid var(--border);border-radius:12px;color:var(--txt);font-size:1rem;text-align:center;letter-spacing:1px;font-weight:700;margin-bottom:1rem;transition:border-color .2s,box-shadow .2s}
.gate-input:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px var(--glow)}
.gate-input::placeholder{color:var(--txt2);font-weight:500;letter-spacing:0}
.gate-btn{width:100%;padding:.9rem;background:linear-gradient(135deg,var(--accent),#8b5cf6);border:none;border-radius:12px;color:#fff;font-weight:800;font-size:1rem;cursor:pointer;transition:transform .15s var(--ease-out-expo),opacity .2s}
.gate-btn:active{transform:scale(.98)}
.gate-btn:disabled{opacity:.5;cursor:not-allowed;transform:none}
.gate-hint{margin-top:.75rem;font-size:.72rem;color:var(--txt2);line-height:1.4}
.gate-hint code{background:var(--bg3);padding:.15rem .4rem;border-radius:6px;border:1px solid var(--border);font-size:.7rem}
/* BULK PANEL expansivel ao lado da logo */
.bulk-toggle{width:40px;height:40px;border-radius:10px;background:var(--bg3);border:1.5px solid var(--border);color:var(--txt);cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:1.15rem;transition:background .2s,border-color .2s;flex-shrink:0}
.bulk-toggle:active{transform:scale(.92)}
.bulk-toggle.open{background:var(--accent);border-color:var(--accent);color:#fff;transform:rotate(90deg)}
.bulk-panel{overflow:hidden;max-height:0;opacity:0;transition:max-height .4s var(--ease-out-expo),opacity .3s,padding .3s;background:var(--bg2);border-top:1px solid transparent}
.bulk-panel.open{max-height:420px;opacity:1;border-top-color:var(--border);padding:.85rem 1rem 1rem}
.bulk-head{display:flex;gap:.5rem;align-items:center;margin-bottom:.65rem;flex-wrap:wrap}
.bulk-search{flex:1;min-width:140px;padding:.55rem .8rem;background:var(--bg3);border:1.5px solid var(--border);border-radius:10px;color:var(--txt);font-size:.82rem;transition:border-color .2s}
.bulk-search:focus{outline:none;border-color:var(--accent)}
.bulk-search::placeholder{color:var(--txt2)}
.bulk-stats{font-size:.75rem;color:var(--txt2);font-weight:700;white-space:nowrap}
.bulk-stats b{color:var(--accent2)}
.course-sel-list{max-height:220px;overflow-y:auto;border:1px solid var(--border);border-radius:10px;background:var(--bg);scrollbar-width:thin}
.course-sel-list::-webkit-scrollbar{width:6px}
.course-sel-list::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
.course-sel-item{display:flex;align-items:center;gap:.6rem;padding:.55rem .75rem;border-bottom:1px solid var(--border);cursor:pointer;transition:background .15s,transform .15s var(--ease-out-expo)}
.course-sel-item:last-child{border-bottom:none}
.course-sel-item:hover{background:var(--bg3)}
.course-sel-item input{width:16px;height:16px;accent-color:var(--accent);flex-shrink:0}
.course-sel-info{flex:1;min-width:0}
.course-sel-name{font-size:.82rem;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.course-sel-count{font-size:.68rem;color:var(--txt2)}
.course-sel-item.selected{background:rgba(108,92,231,.08)}
.bulk-actions{display:flex;gap:.4rem;margin-top:.65rem;flex-wrap:wrap}
.bulk-actions .abtn{flex:1;min-width:90px;padding:.55rem;font-size:.72rem;min-height:38px}
.btn-ghost{background:var(--bg3);color:var(--txt);border:1.5px solid var(--border)}
.bulk-progress{margin-top:.6rem;height:5px;background:var(--bg3);border-radius:3px;overflow:hidden;display:none}
.bulk-progress .bar{height:100%;background:linear-gradient(90deg,var(--accent),#fd79a8);width:0%;transition:width .3s var(--ease-out-expo)}
.bulk-progress-label{margin-top:.3rem;font-size:.7rem;color:var(--txt2);text-align:center;display:none}
html.theme-transitioning,html.theme-transitioning *,html.theme-transitioning *::before,html.theme-transitioning *::after{transition:background-color .4s ease,color .4s ease,border-color .4s ease,box-shadow .4s ease !important}
</style>
<script src="https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/build/pdf.min.js"></script>
</head>
<body>
<div id="idGate" style="display:flex">
  <div class="gate-card">
    <div class="gate-logo">StemPlay Library</div>
    <div class="gate-sub">Digite seu ID para acessar</div>
    <input type="text" id="gateInput" class="gate-input" placeholder="ex: k3s, 3234" autocomplete="off" autocorrect="off" spellcheck="false">
    <button type="button" class="gate-btn" id="gateEnter" onclick="enterWithId(document.getElementById('gateInput').value)">Entrar →</button>
    <div class="gate-hint">O ID será usado em todos os links:<br><code>pdf&amp;userId=SEU_ID</code></div>
  </div>
</div>
<div class="header">
  <div class="header-top">
    <div style="display:flex;align-items:center;gap:.6rem">
      <div class="logo">StemPlay Library</div>
      <button class="bulk-toggle" id="bulkToggle" aria-label="Baixar cursos" title="Baixar cursos">☰</button>
    </div>
    <button class="theme-btn" id="themeBtn" aria-label="Alternar tema">&#9790;</button>
  </div>
  <div class="bulk-panel" id="bulkPanel">
    <div class="bulk-head">
      <input type="text" id="bulkSearch" class="bulk-search" placeholder="Pesquisar curso... ex: english teen2" autocomplete="off" spellcheck="false">
      <div class="bulk-stats"><b id="selCount">0</b> cursos · <b id="selFiles">0</b> livros</div>
    </div>
    <div class="course-sel-list" id="bulkList"></div>
    <div class="bulk-actions">
      <button class="abtn btn-ghost" id="bulkSelAll">Selecionar visíveis</button>
      <button class="abtn btn-ghost" id="bulkClear">Limpar</button>
      <button class="abtn btn-online" id="bulkDownload" style="flex:1.3">⬇ Baixar selecionados</button>
    </div>
    <div class="bulk-progress" id="bulkProgress"><div class="bar" id="bulkBar"></div></div>
    <div class="bulk-progress-label" id="bulkLabel"></div>
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
let savedId=localStorage.getItem('sp_userId');
let userId=savedId||'';
const $=id=>document.getElementById(id);
const $$=(s,p)=>(p||document).querySelectorAll(s);
function hashString(s){let h=0;for(let i=0;i<s.length;i++)h=((h<<5)-h)+s.charCodeAt(i);return Math.abs(h)}
function courseGradient(course){const h=hashString(course);const hue1=h%360;const hue2=(hue1+40)%360;const sat=65+(h%20);const lit=45+(h%15);return`linear-gradient(135deg,hsl(${hue1} ${sat}% ${lit}%) 0%,hsl(${hue2} ${sat}% ${lit-10}%) 100%)`}
let toastTimer;
function toast(m){const t=$('toast');t.textContent=m;t.classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>t.classList.remove('show'),2200)}
const _rafQueue=new Map();
function rafThrottle(key,fn){if(_rafQueue.has(key))return;_rafQueue.set(key,requestAnimationFrame(()=>{fn();_rafQueue.delete(key)}))}
function debounceRAF(fn,delay=16){let rafId=null;let lastArgs=null;return function(...a){lastArgs=a;if(rafId!==null)return;rafId=requestAnimationFrame(()=>{setTimeout(()=>{fn.apply(this,lastArgs);rafId=null},delay)},0)}}
async function downloadPDF(url,name){try{toast('Iniciando download...');const r=await fetch(url);if(!r.ok)throw 0;const b=await r.blob();const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download=name+'.pdf';document.body.appendChild(a);a.click();setTimeout(()=>{a.remove();URL.revokeObjectURL(a.href)},100);toast('Download iniciado')}catch(e){window.open(url,'_blank');toast('Aberto em nova aba')}}
function renderPlaceholder(course,type,url){const letter=course.charAt(0).toUpperCase();const bg=courseGradient(course);const safeUrl=(url||'').replace(/"/g,'&quot;');return`<div class="thumb-wrap" data-pdf="${safeUrl}"><canvas class="thumb-canvas" width="320" height="240"></canvas><div class="placeholder" style="background:${bg}"><div class="ph-letter">${letter}</div><div class="ph-type">${type}</div><div class="ph-course">${course}</div></div></div>`}
const _cardHtmlCache=new Map();function buildCardHtml(i){const k=i.url;if(_cardHtmlCache.has(k))return _cardHtmlCache.get(k);const bc='b-'+i.material_type.toLowerCase();const isF=favs.has(i.url);const onlineUrl='https://reader.stemplay.io/?file='+encodeURIComponent(i.url)+'&userId='+encodeURIComponent(userId||'k3s');let badges=`<span class="badge ${bc}">${i.material_type}</span>`;if(i.module_num)badges+=`<span class="badge" style="background:#8b5cf6;color:#fff">M${i.module_num}</span>`;if(i.unit_num)badges+=`<span class="badge" style="background:#ec4899;color:#fff">U${i.unit_num}</span>`;const h=`${renderPlaceholder(i.course,i.material_type,i.url)}<div class="card-body"><div class="card-name">${i.display_name}</div><div class="card-badges">${badges}</div><div class="card-actions"><a href="${onlineUrl}" target="_blank" rel="noopener" class="abtn btn-online">Online</a><button class="abtn btn-dl">Download</button><button class="abtn btn-fav${isF?' is-fav':''}">${isF?'\\u2605':'\\u2606'}</button></div></div>`;_cardHtmlCache.set(k,h);return h}
function render(){const app=$('app');const frag=document.createDocumentFragment();let vc=0;const sl=cS.toLowerCase();D.forEach(c=>{const fi=c.items.filter(i=>{const ms=!sl||i.course.toLowerCase().includes(sl)||i.display_name.toLowerCase().includes(sl)||i.group_name.toLowerCase().includes(sl);const mf=cF==='all'||i.material_type===cF;if(cV==='fav')return favs.has(i.url);return ms&&mf});if(!fi.length)return;vc+=fi.length;const gs={};fi.forEach(i=>{(gs[i.group_name]=gs[i.group_name]||[]).push(i)});const ce=document.createElement('div');ce.className='course';ce.innerHTML=`<div class="chdr"><div class="ctitle">${c.name}</div><div class="ccount">${fi.length}</div><div class="carrow">&#9660;</div></div><div class="cbody"></div>`;const cb=ce.querySelector('.cbody');Object.entries(gs).forEach(([gn,items])=>{const gt=document.createElement('div');gt.className='gtitle';gt.textContent=gn+' \\u00b7 '+items.length+' itens';cb.appendChild(gt);const gr=document.createElement('div');gr.className='grid';items.forEach(i=>{const a=document.createElement('div');a.className='card '+i.material_type.toLowerCase();a.innerHTML=buildCardHtml(i);a.querySelector('.btn-dl').onclick=e=>{e.stopPropagation();downloadPDF(i.url,i.display_name)};a.querySelector('.btn-fav').onclick=e=>{e.stopPropagation();toggleFav(i.url)};gr.appendChild(a)});cb.appendChild(gr)});ce.querySelector('.chdr').onclick=()=>ce.classList.toggle('open');frag.appendChild(ce)});app.innerHTML='';app.appendChild(frag);$('sT').textContent=D.reduce((s,c)=>s+c.items.length,0);$('sC').textContent=D.length;$('sV').textContent=vc;if(!vc){app.innerHTML=`<div class="empty"><div class="empty-icon">${cV==='fav'?'FAV':'BUSCA'}</div><h3>${cV==='fav'?'Nenhum favorito':'Nada encontrado'}</h3><p style="margin-top:.5rem;font-size:.85rem;color:var(--txt2)">${cV==='fav'?'Toque na estrela para favoritar':'Tente outra busca'}</p></div>`};if(_thumbObserver)try{_thumbObserver.disconnect()}catch(e){}requestIdleCallback(()=>{try{initThumbs()}catch(e){}},{timeout:80})}
function toggleFav(u){if(favs.has(u)){favs.delete(u);toast('Removido dos favoritos')}else{favs.add(u);toast('Adicionado aos favoritos')}localStorage.setItem('sp_favs',JSON.stringify([...favs]));render()}
function toggleTheme(){const html=document.documentElement;const btn=$('themeBtn');html.classList.add('theme-transitioning');const current=html.getAttribute('data-theme');const next=current==='dark'?'light':'dark';html.setAttribute('data-theme',next);localStorage.setItem('sp_theme',next);btn.innerHTML=next==='dark'?'\\u263E':'\\u2600';btn.classList.add('animating');setTimeout(()=>btn.classList.remove('animating'),600);toast(next==='dark'?'Modo escuro':'Modo claro');setTimeout(()=>html.classList.remove('theme-transitioning'),400)}
$('themeBtn').onclick=toggleTheme;
// --- GATE ID - primeira tela obrigatoria (so altera &userId=) ---
function enterWithId(v){const id=(v||'').trim();if(!id){toast('Digite um ID');return false}userId=id;localStorage.setItem('sp_userId',userId);savedId=userId;const gate=$('idGate');if(gate)gate.classList.add('hidden');document.body.style.overflow='';toast('ID: '+userId);render();return true}
try{
  const gate=$('idGate');
  if(gate){
    gate.classList.remove('hidden');
    document.body.style.overflow='hidden';
    if(savedId) $('gateInput').value=savedId;
    setTimeout(()=>{try{$('gateInput').focus();$('gateInput').select()}catch(e){}},200);
  }
  if($('gateEnter'))$('gateEnter').onclick=()=>enterWithId($('gateInput').value);
  if($('gateInput'))$('gateInput').onkeydown=e=>{if(e.key==='Enter')enterWithId(e.target.value)};
}catch(e){}
// --- BULK DOWNLOAD expansivel ao lado da logo ---
let bulkSelected=new Set();
let bulkFilter='';
function getBulkFiltered(){const q=bulkFilter.toLowerCase().trim();return q? D.filter(c=>c.name.toLowerCase().includes(q)) : D}
function updateBulkStats(){const c=$('selCount'), f=$('selFiles'); if(!c||!f) return; c.textContent=bulkSelected.size; let total=0; bulkSelected.forEach(n=>{const course=D.find(x=>x.name===n); if(course) total+=course.items.length}); f.textContent=total; const btn=$('bulkDownload'); if(btn){btn.disabled=bulkSelected.size===0; btn.style.opacity=bulkSelected.size===0?'0.5':'1'; btn.textContent= total? `⬇ Baixar ${total} livro${total>1?'s':''} (${bulkSelected.size} curso${bulkSelected.size>1?'s':''})` : '⬇ Baixar selecionados'}}
function renderBulkList(){const list=$('bulkList'); if(!list) return; const filtered=getBulkFiltered(); list.innerHTML=''; if(!filtered.length){list.innerHTML='<div style="padding:1rem;text-align:center;color:var(--txt2);font-size:.82rem">Nenhum curso encontrado</div>';return} filtered.forEach(course=>{const isSel=bulkSelected.has(course.name); const row=document.createElement('label'); row.className='course-sel-item'+(isSel?' selected':''); const types=[...new Set(course.items.map(i=>i.material_type))].join(', '); row.innerHTML=`<input type="checkbox" ${isSel?'checked':''}><div class="course-sel-info"><div class="course-sel-name">${course.name}</div><div class="course-sel-count">${course.items.length} livros · ${types}</div></div>`; const cb=row.querySelector('input'); const toggle=()=>{if(cb.checked) bulkSelected.add(course.name); else bulkSelected.delete(course.name); renderBulkList(); updateBulkStats()}; cb.onchange=toggle; row.onclick=e=>{if(e.target!==cb){cb.checked=!cb.checked; toggle()}}; list.appendChild(row)}); }
try{
  const t=$('bulkToggle'), p=$('bulkPanel');
  if(t&&p){
    t.onclick=()=>{
      const isOpen=p.classList.contains('open');
      if(isOpen){p.classList.remove('open'); t.classList.remove('open'); t.textContent='☰';}
      else{p.classList.add('open'); t.classList.add('open'); t.textContent='✕'; renderBulkList(); updateBulkStats(); setTimeout(()=>{try{$('bulkSearch').focus()}catch(e){}},150)}
    };
  }
  if($('bulkSearch'))$('bulkSearch').oninput=e=>{bulkFilter=e.target.value; renderBulkList()};
  if($('bulkSelAll'))$('bulkSelAll').onclick=()=>{getBulkFiltered().forEach(c=>bulkSelected.add(c.name)); renderBulkList(); updateBulkStats(); toast('Visíveis selecionados')};
  if($('bulkClear'))$('bulkClear').onclick=()=>{bulkSelected.clear(); renderBulkList(); updateBulkStats(); toast('Seleção limpa')};
  if($('bulkDownload'))$('bulkDownload').onclick=async()=>{
    if(!bulkSelected.size){toast('Selecione ao menos 1 curso');return}
    const files=[]; bulkSelected.forEach(name=>{const co=D.find(x=>x.name===name); if(co) files.push(...co.items.map(it=>({url:it.url, name: co.name+' - '+it.display_name})))} );
    if(!files.length){toast('Nenhum livro');return}
    if(files.length>80 && !confirm(`Você vai baixar ${files.length} livros de ${bulkSelected.size} curso(s).\nO navegador pode pedir permissão para múltiplos downloads.\nContinuar?`)) return;
    const prog=$('bulkProgress'), bar=$('bulkBar'), lab=$('bulkLabel'); if(prog)prog.style.display='block'; if(lab){lab.style.display='block'; lab.textContent=`Iniciando... 0/${files.length}`}; if(bar)bar.style.width='0%'; const btn=$('bulkDownload'); if(btn)btn.disabled=true; let ok=0,err=0;
    for(let i=0;i<files.length;i++){
      const f=files[i]; if(lab) lab.textContent=`Baixando ${i+1}/${files.length}: ${f.name}`; if(bar) bar.style.width=((i/files.length)*100).toFixed(1)+'%';
      try{const r=await fetch(f.url); if(!r.ok) throw new Error(r.status); const blob=await r.blob(); const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download=f.name+'.pdf'; document.body.appendChild(a); a.click(); setTimeout(()=>{a.remove(); URL.revokeObjectURL(a.href)},900); ok++ }catch(e){err++; try{window.open(f.url,'_blank')}catch(e2){}}
      if(i<files.length-1) await new Promise(res=>setTimeout(res,420));
    }
    if(bar)bar.style.width='100%'; if(lab)lab.textContent=`Concluído: ${ok} OK, ${err} em nova aba`; toast(`Lote: ${ok} baixados`); if(btn)btn.disabled=false; setTimeout(()=>{if(prog)prog.style.display='none'; if(lab)lab.style.display='none'; if(bar)bar.style.width='0%'},4000);
  };
}catch(e){}
// --- THUMBNAILS PDF.js lazy (sem baixar milhares no servidor) ---
let thumbCache=new Map();let _thumbObserver=null;
try{if(typeof pdfjsLib!=='undefined')pdfjsLib.GlobalWorkerOptions.workerSrc='https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/build/pdf.worker.min.js'}catch(e){}
async function renderPdfThumb(url,canvas,wrap){if(!url||!canvas||thumbCache.get(url)==='done')return;if(thumbCache.get(url)==='loading')return;thumbCache.set(url,'loading');wrap.classList.add('loading');try{const task=pdfjsLib.getDocument({url:url,rangeChunkSize:65536,withCredentials:false});const pdf=await task.promise;const page=await pdf.getPage(1);const vp=page.getViewport({scale:0.5});const ctx=canvas.getContext('2d');canvas.width=vp.width;canvas.height=vp.height;await page.render({canvasContext:ctx,viewport:vp}).promise;wrap.classList.add('has-thumb');wrap.classList.remove('loading');thumbCache.set(url,'done');try{await pdf.destroy()}catch(e){}}catch(e){thumbCache.delete(url);wrap.classList.remove('loading')}}
function initThumbs(){const wraps=document.querySelectorAll('.thumb-wrap[data-pdf]');if(!wraps.length)return;if(!('IntersectionObserver' in window)){wraps.forEach(w=>{const c=w.querySelector('.thumb-canvas');const u=w.getAttribute('data-pdf');if(c&&u)renderPdfThumb(u,c,w)});return}if(_thumbObserver)try{_thumbObserver.disconnect()}catch(e){}_thumbObserver=new IntersectionObserver(entries=>{entries.forEach(en=>{if(en.isIntersecting){const w=en.target;const c=w.querySelector('.thumb-canvas');const u=w.getAttribute('data-pdf');if(c&&u)renderPdfThumb(u,c,w);_thumbObserver.unobserve(w)}})},{rootMargin:'200px',threshold:0.01});wraps.forEach(w=>_thumbObserver.observe(w))}
const _renderPending={value:false};
function scheduleRender(){if(_renderPending.value)return;_renderPending.value=true;requestAnimationFrame(()=>{render();_renderPending.value=false})}
const _searchInput=$('searchBox');
const _debouncedSearch=debounceRAF(e=>{cS=e.target.value;scheduleRender()},150);
_searchInput.addEventListener('input',_debouncedSearch,{passive:true});
$('filterBar').addEventListener('click',e=>{const b=e.target.closest('.fbtn');if(!b)return;$$('.fbtn').forEach(x=>x.classList.remove('active'));b.classList.add('active');cF=b.dataset.t;scheduleRender()},{passive:true});
$$('.nitem').forEach(b=>b.addEventListener('click',function(){if(this.dataset.a==='top'){window.scrollTo({top:0,behavior:'smooth'});return}$$('.nitem').forEach(x=>x.classList.remove('active'));this.classList.add('active');cV=this.dataset.a;scheduleRender()},{passive:true}));
const savedTheme=localStorage.getItem('sp_theme')||'dark';document.documentElement.setAttribute('data-theme',savedTheme);$('themeBtn').innerHTML=savedTheme==='dark'?'\\u263E':'\\u2600';
render();
console.log('StemPlay Library v12 |',D.reduce((s,c)=>s+c.items.length,0),'materiais em',D.length,'cursos');
</script>
</body>
</html>"""

    html = html_template.replace("{courses_json}", courses_json)
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  [OK] Biblioteca gerada: {output_html}")
    print(f"  [INFO] {len(courses)} cursos | {len(pdfs)} materiais (sem duplicatas)")


if __name__ == "__main__":
    main()
