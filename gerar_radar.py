#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RADAR CRTNG — gerador do painel read-only.
Lê os frontmatters `radar: true` do vault e gera public/index.html.
Uso:  python gerar_radar.py            (usa radar_config.json)
      python gerar_radar.py --no-push  (gera sem git push)
Dependência: pip install pyyaml
"""
import json, re, shutil, subprocess, sys
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("Falta dependência: pip install pyyaml")

BASE = Path(__file__).resolve().parent
cfg = json.loads((BASE / "radar_config.json").read_text(encoding="utf-8"))
VAULT = Path(cfg["vault_path"])
OUT = BASE / cfg.get("output_dir", "public")
FM_RE = re.compile(r"^---\s*\n(.*?)\n---", re.S)
PROG_RE = re.compile(r"^\s*(\d+)\s*/\s*(\d+)\s*(.*)$")

def _clean(v):
    """Remove aspas residuais de patches antigos e normaliza."""
    s = str(v if v is not None else "").strip()
    while len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
        s = s[1:-1].strip()
    return s

def _truthy(v):
    return _clean(v).lower() in ("true", "yes", "sim", "1") or v is True


if not VAULT.is_dir():
    sys.exit(f"vault_path não encontrado: {VAULT}")

frentes = []
for md in VAULT.rglob("*.md"):
    try:
        text = md.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        continue
    m = FM_RE.match(text)
    if not m:
        continue
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        print(f"  ⚠️ YAML inválido, pulando: {md}")
        continue
    if not isinstance(fm, dict) or not _truthy(fm.get("radar")):
        continue
    item = {
        "arquivo": md.relative_to(VAULT).as_posix(),
        "tipo": _clean(fm.get("tipo")),
        "cliente": _clean(fm.get("cliente")) or md.parent.name,
        "status": (_clean(fm.get("status")) or "ativo").lower(),
        "fase": _clean(fm.get("fase")),
        "proxima_acao": _clean(fm.get("proxima_acao")),
        "prazo": _clean(fm.get("prazo")),
        "atualizado": _clean(fm.get("atualizado")),
    }
    pm = PROG_RE.match(_clean(fm.get("progresso")))
    if pm:
        item["progresso"] = {
            "atual": int(pm.group(1)),
            "total": int(pm.group(2)),
            "label": pm.group(3).strip(" ·-—") or "progresso",
        }
    frentes.append(item)

# ativos primeiro, depois por prazo mais próximo, depois nome
frentes.sort(key=lambda f: (f["status"] != "ativo", f["prazo"] or "9999-99-99", f["cliente"]))

template = (BASE / "radar_template.html").read_text(encoding="utf-8")
now = datetime.now()
html = (
    template
    .replace("__GERADO_EM__", now.strftime("%Y-%m-%dT%H:%M:%S"))
    .replace('"__FRENTES__"', json.dumps(frentes, ensure_ascii=False, indent=2))
)

OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(html, encoding="utf-8")
for f in ["manifest.json", "sw.js", "icon-192.png", "icon-512.png"]:
    src = BASE / "pwa" / f
    if src.exists():
        shutil.copy(src, OUT / f)

print(f"OK · {len(frentes)} frentes · gerado {now:%d/%m %H:%M} → {OUT / 'index.html'}")

if cfg.get("git_push") and "--no-push" not in sys.argv:
    for cmd in (["git", "add", "-A"],
                ["git", "commit", "-m", f"radar {now:%Y-%m-%d %H:%M}"],
                ["git", "push"]):
        r = subprocess.run(cmd, cwd=BASE, capture_output=True, text=True)
        if r.returncode != 0 and "nothing to commit" not in (r.stdout + r.stderr):
            print(f"  ⚠️ git: {' '.join(cmd)} → {(r.stderr or r.stdout).strip()[:200]}")
            break
    else:
        print("  ↑ publicado (git push → Vercel faz o deploy)")
