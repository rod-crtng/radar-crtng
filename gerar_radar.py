#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RADAR CRTNG — gerador do painel read-only.
Lê os frontmatters `radar: true` do vault e gera public/index.html.
Uso:  python gerar_radar.py            (usa radar_config.json)
      python gerar_radar.py --no-push  (gera sem git push)
Dependência: pip install pyyaml
"""
import json, re, shutil, subprocess, sys, hashlib
from datetime import datetime, date
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

def _iso_date(v):
    """Aceita date do YAML (2026-06-14) ou string e devolve 'YYYY-MM-DD'."""
    if isinstance(v, (date, datetime)):
        return v.isoformat()[:10]
    return _clean(v)[:10]

def _parse_eventos(raw):
    """Normaliza o campo `eventos` (lista de {data, tipo, titulo, obs})."""
    out = []
    if not isinstance(raw, list):
        return out
    for e in raw:
        if not isinstance(e, dict):
            continue
        d = _iso_date(e.get("data"))
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", d):
            continue
        out.append({
            "data": d,
            "tipo": (_clean(e.get("tipo")) or "outro").lower(),
            "titulo": _clean(e.get("titulo")) or _clean(e.get("title")),
            "obs": _clean(e.get("obs")),
        })
    out.sort(key=lambda x: x["data"])
    return out


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
        "prazo": _iso_date(fm.get("prazo")) if fm.get("prazo") else "",
        "atualizado": _iso_date(fm.get("atualizado")) if fm.get("atualizado") else "",
        "eventos": _parse_eventos(fm.get("eventos")),
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

# === GATE DE MUDANÇA ===
# Hash do que realmente importa: os dados (frentes) + o template (com placeholders).
# O timestamp de geração NÃO entra no hash, então rodar o script sem mudança real
# não republica nada — mata commit/deploy redundante. `--force` ignora o gate.
payload = json.dumps(frentes, ensure_ascii=False, sort_keys=True)
novo_hash = hashlib.sha256((payload + template).encode("utf-8")).hexdigest()[:16]

def _hash_publicado(idx):
    if not idx.exists():
        return None
    try:
        m = re.search(r"radar-hash:\s*([0-9a-f]+)", idx.read_text(encoding="utf-8"))
    except OSError:
        return None
    return m.group(1) if m else None

forcar = "--force" in sys.argv
hash_atual = _hash_publicado(OUT / "index.html")
mudou = forcar or (novo_hash != hash_atual)

if not mudou:
    print(f"sem mudanças (hash {novo_hash}) · radar não republicado")
    sys.exit(0)

now = datetime.now()
html = (
    template
    .replace("__GERADO_EM__", now.strftime("%Y-%m-%dT%H:%M:%S"))
    .replace("__HASH__", novo_hash)
    .replace('"__FRENTES__"', json.dumps(frentes, ensure_ascii=False, indent=2))
)

OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(html, encoding="utf-8")
for f in ["manifest.json", "sw.js", "icon-192.png", "icon-512.png"]:
    src = BASE / "pwa" / f
    if src.exists():
        shutil.copy(src, OUT / f)

motivo = "forçado" if forcar else "mudança detectada"
print(f"OK · {len(frentes)} frentes · {motivo} (hash {novo_hash}) · gerado {now:%d/%m %H:%M} → {OUT / 'index.html'}")

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
