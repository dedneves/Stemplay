#!/usr/bin/env python3
"""
StemPlay Library Premium - Mobile-First com Performance Real
"""

from urllib.parse import quote
import re
from pathlib import Path
from collections import defaultdict
import json

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
    
    courses = [{"name": name, "items": sorted(items, key=lambda x: x['sort_key'])} 
               for name, items in sorted(courses_dict.items())]
    
    courses_json = json.dumps(courses, ensure_ascii=False)
    
    print("🎨 Gerando biblioteca premium...")
    
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<meta name="theme-color" content="#0f0f23">
<title>📚 StemPlay Library</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📚</text></svg>">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }}
:root {{
  --bg-primary: #0f0f23; --bg-secondary: #1a1a2e; --bg-tertiary: #16213e;
  --accent: #00d4ff; --accent-glow: rgba(0, 212, 255, 0.3);
  --text-primary: #ffffff; --text-secondary: #a0a0b0;
  --card-bg: #1e1e3f; --border: #2a2a4e;
  --success: #10b981; --warning: #f59e0b;
}}
html[data-theme="light"] {{
  --bg-primary: #f5f7fa; --bg-secondary: #ffffff; --bg-tertiary: #e8ecf3;
  --accent: #0066cc; --text-primary: #1a1a2e; --text-secondary: #555;
  --card-bg: #ffffff; --border: #dde1e8;
}}
body {{ font-family: -apple-system, sans-serif; background: var(--bg-primary); color: var(--text-primary); min-height: 100vh; padding-bottom: 70px; transition: all 0.3s; }}
.header {{ position: sticky; top: 0; background: var(--bg-secondary); border-bottom: 1px solid var(--border); z-index: 100; backdrop-filter: blur(20px); }}
.header-top {{ display: flex; justify-content: space-between; padding: 1rem; }}
.logo {{ font-size: 1.25rem; font-weight: 800; background: linear-gradient(135deg, var(--accent) 0%, #ff00ff 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
.icon-btn {{ width: 40px; height: 40px; border-radius: 50%; background: var(--bg-tertiary); border: none; color: var(--text-primary); cursor: pointer; font-size: 1.2rem; }}
.stats-bar {{ display: flex; gap: 0.5rem; padding: 0 1rem 0.75rem; overflow-x: auto; }}
.stat-chip {{ background: var(--bg-tertiary); padding: 0.4rem 0.8rem; border-radius: 20px; font-size: 0.75rem; border: 1px solid var(--border); }}
.stat-chip strong {{ color: var(--accent); }}
.search-container {{ padding: 0 1rem 0.75rem; }}
.search-input {{ width: 100%; padding: 0.875rem 1rem; background: var(--bg-tertiary); border: 2px solid var(--border); border-radius: 12px; color: var(--text-primary); font-size: 1rem; }}
.search-input:focus {{ outline: none; border-color: var(--accent); }}
.filters {{ display: flex; gap: 0.5rem; padding: 0 1rem 1rem; overflow-x: auto; }}
.filter-btn {{ padding: 0.5rem 1rem; background: var(--bg-tertiary); border: 1.5px solid var(--border); border-radius: 20px; color: var(--text-secondary); cursor: pointer; font-weight: 600; font-size: 0.875rem; white-space: nowrap; }}
.filter-btn.active {{ background: var(--accent); color: var(--bg-primary); }}
.main {{ padding: 0 0.75rem; }}
.course {{ background: var(--bg-secondary); border-radius: 16px; margin-bottom: 0.75rem; border: 1px solid var(--border); }}
.course-header {{ padding: 1rem; cursor: pointer; display: flex; justify-content: space-between; align-items: center; }}
.course-title {{ font-size: 1rem; font-weight: 700; flex: 1; }}
.course-count {{ background: var(--accent); color: var(--bg-primary); padding: 0.25rem 0.6rem; border-radius: 12px; font-size: 0.75rem; font-weight: 700; }}
.course-content {{ display: none; padding: 0 1rem 1rem; }}
.course.expanded .course-content {{ display: block; }}
.group-title {{ color: var(--accent); font-size: 0.875rem; font-weight: 700; margin: 0.75rem 0 0.5rem; text-transform: uppercase; }}
.pdfs-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 0.5rem; }}
.pdf-card {{ background: var(--card-bg); border-radius: 12px; padding: 0.875rem; text-decoration: none; color: var(--text-primary); border: 1.5px solid var(--border); display: flex; align-items: center; gap: 0.75rem; }}
.pdf-card:active {{ transform: scale(0.97); }}
.pdf-icon {{ font-size: 1.5rem; }}
.pdf-info {{ flex: 1; }}
.pdf-name {{ font-weight: 600; font-size: 0.9rem; margin-bottom: 0.25rem; }}
.badge {{ padding: 0.15rem 0.5rem; border-radius: 10px; font-size: 0.65rem; font-weight: 700; text-transform: uppercase; }}
.badge-teacher {{ background: var(--warning); color: var(--bg-primary); }}
.badge-workbook {{ background: var(--success); color: var(--bg-primary); }}
.badge-standard, .badge-student {{ background: var(--accent); color: var(--bg-primary); }}
.bottom-nav {{ position: fixed; bottom: 0; left: 0; right: 0; background: var(--bg-secondary); border-top: 1px solid var(--border); display: flex; justify-content: space-around; padding: 0.5rem 0; z-index: 100; }}
.nav-item {{ background: none; border: none; color: var(--text-secondary); padding: 0.5rem; cursor: pointer; text-align: center; font-size: 0.7rem; }}
.nav-item.active {{ color: var(--accent); }}
.nav-icon {{ font-size: 1.5rem; display: block; }}
.toast {{ position: fixed; bottom: 90px; left: 50%; transform: translateX(-50%); background: var(--bg-secondary); padding: 0.75rem 1.25rem; border-radius: 25px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); z-index: 1000; opacity: 0; transition: opacity 0.3s; pointer-events: none; }}
.toast.show {{ opacity: 1; }}
@media (min-width: 768px) {{ body {{ padding-bottom: 0; }} .bottom-nav {{ display: none; }} .main {{ max-width: 1400px; margin: 0 auto; padding: 0 2rem; }} }}
</style>
</head>
<body>
<div class="header">
  <div class="header-top">
    <div class="logo">📚 StemPlay Library</div>
    <button class="icon-btn" id="themeToggle">🌓</button>
  </div>
  <div class="stats-bar">
    <div class="stat-chip"><strong id="statTotal">0</strong> materiais</div>
    <div class="stat-chip"><strong id="statCourses">0</strong> cursos</div>
    <div class="stat-chip"><strong id="statVisible">0</strong> visíveis</div>
  </div>
  <div class="search-container">
    <input type="text" class="search-input" id="searchBox" placeholder="🔍 Buscar..." autocomplete="off">
  </div>
  <div class="filters">
    <button class="filter-btn active" data-type="all">Todos</button>
    <button class="filter-btn" data-type="Standard">📖 Padrão</button>
    <button class="filter-btn" data-type="Teacher">👨‍🏫 Teacher</button>
    <button class="filter-btn" data-type="Workbook">📝 Workbook</button>
    <button class="filter-btn" data-type="Student">🎓 Student</button>
  </div>
</div>
<div class="main" id="mainContent"></div>
<div class="bottom-nav">
  <button class="nav-item active" data-action="home"><span class="nav-icon">🏠</span>Início</button>
  <button class="nav-item" data-action="courses"><span class="nav-icon">📚</span>Cursos</button>
  <button class="nav-item" data-action="favorites"><span class="nav-icon">⭐</span>Favoritos</button>
  <button class="nav-item" data-action="top"><span class="nav-icon">⬆️</span>Topo</button>
</div>
<div class="toast" id="toast"></div>
<script>
const COURSES_DATA = {courses_json};
let currentFilter = 'all', currentSearch = '', currentView = 'home';
let favorites = JSON.parse(localStorage.getItem('stemplay_favs') || '[]');
function showToast(msg) {{ const t = document.getElementById('toast'); t.textContent = msg; t.classList.add('show'); setTimeout(() => t.classList.remove('show'), 2500); }}
function renderLibrary() {{
  const main = document.getElementById('mainContent');
  main.innerHTML = '';
  let visibleCount = 0;
  const searchLower = currentSearch.toLowerCase();
  COURSES_DATA.forEach(course => {{
    const filteredItems = course.items.filter(item => {{
      const matchesSearch = !searchLower || item.course.toLowerCase().includes(searchLower) || item.display_name.toLowerCase().includes(searchLower);
      const matchesFilter = currentFilter === 'all' || item.material_type === currentFilter;
      if (currentView === 'favorites') return favorites.includes(item.url);
      return matchesSearch && matchesFilter;
    }});
    if (filteredItems.length === 0) return;
    visibleCount += filteredItems.length;
    const groups = {{}};
    filteredItems.forEach(item => {{ if (!groups[item.group_name]) groups[item.group_name] = []; groups[item.group_name].push(item); }});
    const courseEl = document.createElement('div');
    courseEl.className = 'course';
    courseEl.innerHTML = `<div class="course-header"><div class="course-title">${{course.name}}</div><div class="course-count">${{filteredItems.length}}</div></div><div class="course-content"></div>`;
    const content = courseEl.querySelector('.course-content');
    Object.entries(groups).forEach(([groupName, items]) => {{
      const title = document.createElement('div');
      title.className = 'group-title';
      title.textContent = `${{groupName}} · ${{items.length}} itens`;
      content.appendChild(title);
      const grid = document.createElement('div');
      grid.className = 'pdfs-grid';
      items.forEach(item => {{
        const card = document.createElement('a');
        card.href = `https://reader.stemplay.io/?file=${{encodeURIComponent(item.url)}}&userId=k3s`;
        card.target = '_blank';
        card.className = `pdf-card ${{item.material_type.toLowerCase()}}`;
        const icon = item.material_type === 'Teacher' ? '👨‍🏫' : item.material_type === 'Workbook' ? '📝' : item.material_type === 'Student' ? '🎓' : '📖';
        const isFav = favorites.includes(item.url);
        card.innerHTML = `<div class="pdf-icon">${{icon}}</div><div class="pdf-info"><div class="pdf-name">${{item.display_name}}</div><span class="badge badge-${{item.material_type.toLowerCase()}}">${{item.material_type}}</span></div><button class="fav-btn" style="background:none;border:none;font-size:1.25rem;cursor:pointer;">${{isFav ? '⭐' : '☆'}}</button>`;
        card.querySelector('.fav-btn').addEventListener('click', (e) => {{ e.preventDefault(); e.stopPropagation(); toggleFavorite(item.url); }});
        grid.appendChild(card);
      }});
      content.appendChild(grid);
    }});
    courseEl.querySelector('.course-header').addEventListener('click', () => courseEl.classList.toggle('expanded'));
    main.appendChild(courseEl);
  }});
  document.getElementById('statTotal').textContent = COURSES_DATA.reduce((s, c) => s + c.items.length, 0);
  document.getElementById('statCourses').textContent = COURSES_DATA.length;
  document.getElementById('statVisible').textContent = visibleCount;
}}
function toggleFavorite(url) {{
  const idx = favorites.indexOf(url);
  if (idx >= 0) {{ favorites.splice(idx, 1); showToast('Removido dos favoritos'); }}
  else {{ favorites.push(url); showToast('⭐ Adicionado!'); }}
  localStorage.setItem('stemplay_favs', JSON.stringify(favorites));
  renderLibrary();
}}
document.getElementById('themeToggle').addEventListener('click', () => {{
  const current = document.documentElement.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('stemplay_theme', next);
  showToast(`Tema ${{next}} 🌓`);
}});
document.getElementById('searchBox').addEventListener('input', (e) => {{ currentSearch = e.target.value; renderLibrary(); }});
document.querySelectorAll('.filter-btn').forEach(btn => btn.addEventListener('click', function() {{
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  this.classList.add('active');
  currentFilter = this.dataset.type;
  renderLibrary();
}}));
document.querySelectorAll('.nav-item').forEach(btn => btn.addEventListener('click', function() {{
  if (this.dataset.action === 'top') {{ window.scrollTo({{ top: 0, behavior: 'smooth' }}); return; }}
  document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
  this.classList.add('active');
  currentView = this.dataset.action;
  renderLibrary();
}}));
document.documentElement.setAttribute('data-theme', localStorage.getItem('stemplay_theme') || 'dark');
renderLibrary();
</script>
</body>
</html>"""
    
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"✅ Biblioteca gerada: {output_html}")
    print(f"📊 {len(courses)} cursos | {len(pdfs)} materiais")

if __name__ == "__main__":
    main()
