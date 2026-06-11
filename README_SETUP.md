# RADAR CRTNG — Kit de publicação

Painel read-only gerado a partir dos frontmatters `radar: true` do vault.
Fluxo de mão única: vault → script → painel. Nada volta da web pro vault.

---

## PARTE 1 — Subir HOJE (10 min, sem instalar nada)

A pasta `public/` já contém o painel pronto com os dados reais de 10/06.

1. Acesse https://vercel.com/new (mesma conta do PORTAL)
2. Na área de deploy, **arraste a pasta `public/`** inteira
3. Nome do projeto: `radar-crtng` → Deploy
4. Pronto: `https://radar-crtng.vercel.app` (ou similar)

**Instalar como app no celular:**
- iPhone: abrir no Safari → Compartilhar → "Adicionar à Tela de Início"
- Android: abrir no Chrome → menu ⋮ → "Instalar app"

Manda o link pro Lucas com a mesma instrução.

> Privacidade: a página tem `noindex` (não aparece em buscador) e os
> frontmatters não carregam valores financeiros (regra do ADR 10/06).
> A URL é o segredo — não publicar em lugar público.

---

## PARTE 2 — Automação diária (20–30 min, quando quiser)

### 2.1 Dependência (uma vez)
```
pip install pyyaml
```

### 2.2 Configurar
Edite `radar_config.json` — confira o caminho do vault:
```json
{
  "vault_path": "D:/BUSINESS/Creating/BRAIN CRTNG/OBSIDIAN CRTNG/CRTNG_BRAIN",
  "output_dir": "public",
  "git_push": false
}
```

### 2.3 Testar manual
```
cd D:\caminho\do\radar_kit
python gerar_radar.py --no-push
```
Deve imprimir `OK · N frentes`. Abra `public/index.html` no navegador e confira.

### 2.4 Ligar no repositório (deploy automático)
1. Crie um repositório **privado** no GitHub (ex.: `crtng/radar`)
2. Na pasta do kit:
   ```
   git init
   git remote add origin https://github.com/SEU_USUARIO/radar.git
   git add -A && git commit -m "radar inicial" && git push -u origin main
   ```
3. No Vercel: Add New Project → Import do repo `radar` →
   **Root Directory: `public`** → Deploy
4. Em `radar_config.json`, mude `"git_push": true`
5. A partir daqui: rodar o script = push = Vercel publica sozinho

### 2.5 Agendar (diário, 08h00)
Prompt de comando **como administrador**:
```
schtasks /Create /SC DAILY /ST 08:00 /TN "CRTNG_RADAR" /TR "python D:\caminho\do\radar_kit\gerar_radar.py"
```
Rodar sob demanda a qualquer momento:
```
schtasks /Run /TN "CRTNG_RADAR"
```
(Se o PC estiver desligado às 08h, o painel fica com o estado do último build —
o carimbo "atualizado há Xd" nos cards denuncia honestamente.)

---

## Como o radar cresce

Pra uma frente nova aparecer no painel: adicionar o bloco de frontmatter
(8 campos + `progresso` opcional, ver ADR `2026-06-10_frontmatter-radar`)
no arquivo canônico do cliente. Nada além disso — o script descobre sozinho
qualquer arquivo com `radar: true` no vault inteiro.

## Estrutura do kit
```
radar_kit/
├── gerar_radar.py        ← o gerador (script único)
├── radar_template.html   ← template do painel (identidade CRTNG)
├── radar_config.json     ← caminho do vault + opções
├── README_SETUP.md       ← este arquivo
├── pwa/                  ← manifest, service worker, ícones
└── public/               ← SAÍDA — é isto que vai pro ar
```
