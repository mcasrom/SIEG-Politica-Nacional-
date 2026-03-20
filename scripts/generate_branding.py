#!/usr/bin/env python3
"""
generate_branding.py
SIEG – Centro OSINT · Política Nacional

Genera assets de branding:
- sieg_logo.svg        → logo para el dashboard
- telegram_banner.svg  → cabecera canal Telegram (1280x640)
- favicon.ico          → favicon para Streamlit

Autor : M. Castillo · mybloggingnotes@gmail.com
© 2026 M. Castillo
"""

import os

BASE_DIR   = os.path.expanduser("~/SIEG-Politica-Nacional")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

# ── Logo principal (dashboard header) ────────────────────
LOGO_SVG = '''<svg width="600" height="180" viewBox="0 0 600 180" xmlns="http://www.w3.org/2000/svg">
<style>
@keyframes scan{0%{opacity:.15}50%{opacity:.55}100%{opacity:.15}}
@keyframes blink{0%,100%{opacity:1}49%{opacity:1}50%{opacity:0}99%{opacity:0}}
.scan{animation:scan 3s ease-in-out infinite}
.cur{animation:blink 1.1s step-end infinite}
</style>
<rect width="600" height="180" rx="4" fill="#0a0e0a" stroke="#1a2e1a"/>
<rect width="600" height="180" rx="4" fill="none" stroke="#00ff41" stroke-width="0.5" opacity="0.3"/>
<line x1="0" y1="32" x2="600" y2="32" stroke="#00ff41" stroke-width="0.3" opacity="0.2"/>
<circle cx="18" cy="16" r="5" fill="#ff5f57"/>
<circle cx="36" cy="16" r="5" fill="#febc2e"/>
<circle cx="54" cy="16" r="5" fill="#28c840"/>
<text x="300" y="22" text-anchor="middle" font-family="monospace" font-size="11" fill="#00ff41" opacity="0.4">sieg-osint-politica-nacional</text>
<rect x="16" y="48" width="568" height="1" fill="#00ff41" opacity="0.08" class="scan"/>
<rect x="16" y="80" width="568" height="1" fill="#00ff41" opacity="0.08" class="scan" style="animation-delay:1s"/>
<rect x="16" y="112" width="568" height="1" fill="#00ff41" opacity="0.08" class="scan" style="animation-delay:2s"/>
<text x="20" y="62" font-family="monospace" font-size="11" fill="#00ff41" opacity="0.5">root@sieg:~$</text>
<text x="112" y="62" font-family="monospace" font-size="11" fill="#00ff41">./radar --mode=osint --target=politica-es</text>
<text x="20" y="82" font-family="monospace" font-size="10" fill="#4ade80" opacity="0.7">[+] Fuentes: 38  |  Partidos: 16  |  Pipeline: OK</text>
<text x="20" y="98" font-family="monospace" font-size="10" fill="#4ade80" opacity="0.7">[+] Narrativas: 9  |  Confianza: 83/100  |  LIVE</text>
<text x="20" y="128" font-family="monospace" font-size="28" font-weight="bold" fill="#00ff41" letter-spacing="8">SIEG</text>
<text x="180" y="128" font-family="monospace" font-size="16" fill="#00cc33" letter-spacing="2">Centro OSINT</text>
<text x="180" y="148" font-family="monospace" font-size="12" fill="#009922" opacity="0.8">Politica Nacional · Espana</text>
<text x="20" y="168" font-family="monospace" font-size="9" fill="#00ff41" opacity="0.35">© 2026 M.Castillo · mybloggingnotes@gmail.com</text>
<rect x="530" y="148" width="52" height="16" rx="2" fill="none" stroke="#00ff41" stroke-width="0.5" opacity="0.4"/>
<text x="556" y="159" font-family="monospace" font-size="9" fill="#00ff41" text-anchor="middle">LIVE</text>
<circle cx="534" cy="156" r="3" fill="#00ff41" opacity="0.7" class="scan"/>
</svg>'''

# ── Banner Telegram (1280x640) ───────────────────────────
TELEGRAM_SVG = '''<svg width="1280" height="640" viewBox="0 0 1280 640" xmlns="http://www.w3.org/2000/svg">
<rect width="1280" height="640" fill="#0a0e0a"/>
<rect width="1280" height="640" fill="none" stroke="#00ff41" stroke-width="2" opacity="0.2"/>
<line x1="0" y1="80" x2="1280" y2="80" stroke="#00ff41" stroke-width="0.5" opacity="0.15"/>
<line x1="0" y1="560" x2="1280" y2="560" stroke="#00ff41" stroke-width="0.5" opacity="0.15"/>
<text x="640" y="180" text-anchor="middle" font-family="monospace" font-size="18" fill="#00ff41" opacity="0.35">root@sieg:~$ ./radar --mode=osint --target=politica-nacional --live</text>
<text x="640" y="310" text-anchor="middle" font-family="monospace" font-size="96" font-weight="bold" fill="#00ff41" letter-spacing="20">SIEG</text>
<text x="640" y="380" text-anchor="middle" font-family="monospace" font-size="32" fill="#00cc33" letter-spacing="6">CENTRO OSINT</text>
<text x="640" y="430" text-anchor="middle" font-family="monospace" font-size="22" fill="#009922" opacity="0.8">Vigilancia Narrativa · Politica Nacional · Espana</text>
<line x1="240" y1="455" x2="1040" y2="455" stroke="#00ff41" stroke-width="0.5" opacity="0.3"/>
<text x="640" y="490" text-anchor="middle" font-family="monospace" font-size="16" fill="#00ff41" opacity="0.5">politica-nacional-osint.streamlit.app</text>
<text x="640" y="520" text-anchor="middle" font-family="monospace" font-size="14" fill="#00ff41" opacity="0.3">© 2026 M. Castillo · mybloggingnotes@gmail.com</text>
<rect x="40" y="40" width="8" height="8" fill="#00ff41" opacity="0.4"/>
<rect x="1232" y="40" width="8" height="8" fill="#00ff41" opacity="0.4"/>
<rect x="40" y="592" width="8" height="8" fill="#00ff41" opacity="0.4"/>
<rect x="1232" y="592" width="8" height="8" fill="#00ff41" opacity="0.4"/>
<text x="56" y="52" font-family="monospace" font-size="11" fill="#00ff41" opacity="0.3">[OSINT]</text>
<text x="56" y="608" font-family="monospace" font-size="11" fill="#00ff41" opacity="0.3">[LIVE]</text>
</svg>'''

# ── Favicon SVG (32x32) ──────────────────────────────────
FAVICON_SVG = '''<svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
<rect width="32" height="32" rx="4" fill="#0a0e0a"/>
<text x="16" y="22" text-anchor="middle" font-family="monospace" font-size="14" font-weight="bold" fill="#00ff41">S</text>
</svg>'''

# Guardar archivos
files = {
    "sieg_logo.svg":       LOGO_SVG,
    "telegram_banner.svg": TELEGRAM_SVG,
    "favicon.svg":         FAVICON_SVG,
}

for fname, content in files.items():
    path = os.path.join(ASSETS_DIR, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Generado: {path}")

# Copiar logo al dashboard
import shutil
shutil.copy(
    os.path.join(ASSETS_DIR, "sieg_logo.svg"),
    os.path.join(BASE_DIR, "dashboard", "sieg_logo.svg")
)
print("Logo copiado a dashboard/")

print("\nAssets generados en:", ASSETS_DIR)
print("Siguiente paso: subir telegram_banner.svg como foto del canal @sieg_politica")
