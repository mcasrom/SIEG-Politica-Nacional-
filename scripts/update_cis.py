#!/usr/bin/env python3
"""
update_cis.py
SIEG - Centro OSINT · Política Nacional

Actualización automática mensual de valoraciones CIS.
Cron: día 20 de cada mes a las 08:05
5 8 20 * * cd ~/SIEG-Politica-Nacional && source venv/bin/activate && python3 scripts/update_cis.py >> logs/cis_update.log 2>&1

Autor : M. Castillo · mybloggingnotes@gmail.com
© 2026 M. Castillo
"""

import os
import json
import re
import requests
from datetime import datetime as dt

BASE_DIR = os.path.expanduser("~/SIEG-Politica-Nacional")
CFG_PATH = os.path.join(BASE_DIR, "config", "politica_config.json")
LOG_PATH = os.path.join(BASE_DIR, "logs", "pipeline.log")

MESES_ES = {
    "01": "enero",   "02": "febrero",  "03": "marzo",
    "04": "abril",   "05": "mayo",     "06": "junio",
    "07": "julio",   "08": "agosto",   "09": "septiembre",
    "10": "octubre", "11": "noviembre","12": "diciembre"
}

# Patrones de extracción de texto web
PATRONES = [
    (r"[Ss]ánchez[^0-9]{1,60}(\d[\.,]\d{1,2})",        "Pedro Sánchez"),
    (r"[Ff]eij[oó]o[^0-9]{1,60}(\d[\.,]\d{1,2})",      "Alberto Núñez Feijóo"),
    (r"[Yy]olanda\s+[Dd]í?az[^0-9]{1,60}(\d[\.,]\d{1,2})", "Yolanda Díaz"),
    (r"[Aa]bascal[^0-9]{1,60}(\d[\.,]\d{1,2})",         "Santiago Abascal"),
]

def log(msg):
    ts = dt.now().isoformat()
    line = f"[{ts}] [CIS] {msg}\n"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line)
    print(msg)

def get_mes_actual():
    return dt.now().strftime("%Y-%m")

def ya_actualizado(cfg, mes):
    for lider, info in cfg.get("cis_valoracion", {}).items():
        hist = info.get("historico", {})
        if mes in hist and hist[mes] is not None:
            return True
    return False

def extraer_valoraciones(texto):
    resultados = {}
    for patron, lider in PATRONES:
        m = re.search(patron, texto)
        if m:
            try:
                val = float(m.group(1).replace(",", "."))
                if 0.0 <= val <= 10.0:
                    resultados[lider] = val
            except ValueError:
                pass
    return resultados

def buscar_datos_cis(mes):
    anyo, num_mes = mes.split("-")
    mes_nombre = MESES_ES.get(num_mes, "")
    headers = {"User-Agent": "Mozilla/5.0 (compatible; SIEG-Bot/1.0)"}
    resultados = {}

    urls = [
        f"https://www.cis.es/es/w/barometro-de-{mes_nombre}-{anyo}",
        "https://www.cis.es",
    ]

    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                found = extraer_valoraciones(r.text)
                for lider, val in found.items():
                    if lider not in resultados:
                        resultados[lider] = val
                        log(f"  {lider}: {val} ({url})")
        except Exception as e:
            log(f"  Error accediendo {url}: {e}")

        if len(resultados) >= 3:
            break

    return resultados

def actualizar_config(cfg, mes, datos):
    cis = cfg.get("cis_valoracion", {})
    n = 0
    for lider, valor in datos.items():
        if lider in cis:
            cis[lider]["historico"][mes] = valor
            n += 1
            log(f"  Config actualizado: {lider} = {valor} ({mes})")
    cfg["cis_valoracion"] = cis
    cfg["cis_meta"]["ultimo_barometro"] = mes
    cfg["cis_meta"]["ultima_actualizacion"] = dt.now().isoformat()
    return n

def main():
    log("=" * 50)
    log("Iniciando actualización automática CIS")

    with open(CFG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    mes = get_mes_actual()
    log(f"Mes objetivo: {mes}")

    if ya_actualizado(cfg, mes):
        log(f"Datos de {mes} ya presentes. Sin cambios.")
        log("=" * 50)
        return

    log(f"Buscando datos CIS para {mes}...")
    datos = buscar_datos_cis(mes)

    if not datos:
        log("AVISO: No se encontraron datos automáticamente.")
        log("Actualización manual necesaria:")
        log(f"  nano {CFG_PATH}")
        log(f"  URL CIS: https://www.cis.es")
        log("=" * 50)
        return

    n = actualizar_config(cfg, mes, datos)

    with open(CFG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

    log(f"OK: {n} lideres actualizados para {mes}")

    # Push a GitHub
    ret = os.system(
        f"cd {BASE_DIR} && "
        f"git add config/politica_config.json && "
        f"git commit -m 'data: CIS actualizado {mes}' && "
        f"git push origin main"
    )
    if ret == 0:
        log("Push GitHub OK")
    else:
        log("AVISO: Push GitHub falló — revisar manualmente")

    log("=" * 50)

if __name__ == "__main__":
    main()
