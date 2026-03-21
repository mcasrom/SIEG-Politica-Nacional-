#!/usr/bin/env python3
"""
auto_diagnostico.py
SIEG – Centro OSINT · Política Nacional

Script de auto-diagnóstico autónomo con aprendizaje adaptativo.
- Mide métricas del sistema cada ejecución
- Guarda histórico en JSON
- Aprende umbrales normales (media ± 2σ)
- Detecta anomalías y envía alertas Telegram
- Se vuelve más preciso con el tiempo

Cron: cada 6 horas
0 */6 * * * cd ~/SIEG-Politica-Nacional && source venv/bin/activate && python3 scripts/auto_diagnostico.py >> logs/diagnostico.log 2>&1

Autor : M. Castillo · mybloggingnotes@gmail.com
© 2026 M. Castillo
"""

import os
import json
import math
import sqlite3
import subprocess
from datetime import datetime, timedelta

import requests

BASE_DIR    = os.path.expanduser("~/SIEG-Politica-Nacional")
NR_DIR      = os.path.expanduser("~/narrative-radar")
LOG_PATH    = os.path.join(BASE_DIR, "logs", "diagnostico.log")
HIST_PATH   = os.path.join(BASE_DIR, "data", "diagnostico_historico.json")
BOT_TOKEN   = "8789958560:AAGRB5opW11gL6m13cXwUAjJcr_bZN2Y9fM"
CHANNEL     = "@sieg_politica"

# Número mínimo de muestras para activar aprendizaje
MIN_MUESTRAS = 7

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [DIAG] {msg}"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line)

def send_telegram(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": CHANNEL, "text": msg,
                  "parse_mode": "HTML", "disable_web_page_preview": True},
            timeout=15
        )
    except Exception as e:
        log(f"Telegram error: {e}")

def cargar_historico():
    if os.path.exists(HIST_PATH):
        with open(HIST_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"muestras": [], "umbrales": {}, "anomalias": []}

def guardar_historico(hist):
    with open(HIST_PATH, "w", encoding="utf-8") as f:
        json.dump(hist, f, ensure_ascii=False, indent=2)

def media_std(valores):
    if len(valores) < 2:
        return 0, 0
    n = len(valores)
    media = sum(valores) / n
    varianza = sum((x - media) ** 2 for x in valores) / n
    return media, math.sqrt(varianza)

def aprender_umbrales(hist):
    """Calcula umbrales adaptativos basados en histórico."""
    muestras = hist["muestras"]
    if len(muestras) < MIN_MUESTRAS:
        return {}

    metricas = {}
    claves = [k for k in muestras[0].keys() if k != "ts"]

    for clave in claves:
        vals = [m[clave] for m in muestras if clave in m and m[clave] is not None]
        if len(vals) >= MIN_MUESTRAS:
            media, std = media_std(vals)
            metricas[clave] = {
                "media": round(media, 3),
                "std":   round(std, 3),
                "min":   round(media - 2 * std, 3),
                "max":   round(media + 2 * std, 3),
                "n":     len(vals)
            }

    return metricas

def medir_metricas():
    """Recoge todas las métricas del sistema."""
    ts  = datetime.now().isoformat()
    m   = {"ts": ts}
    alertas = []

    # ── Disco ─────────────────────────────────────────────
    try:
        result = subprocess.run(
            ["df", "/", "--output=pcent,used,avail"],
            capture_output=True, text=True
        )
        lines = result.stdout.strip().split("\n")
        if len(lines) > 1:
            parts = lines[1].split()
            m["disco_pct"]  = float(parts[0].replace("%", ""))
            m["disco_used_gb"] = round(int(parts[1]) / 1024 / 1024, 2)
            m["disco_free_gb"] = round(int(parts[2]) / 1024 / 1024, 2)
    except Exception as e:
        log(f"Error disco: {e}")

    # ── RAM ───────────────────────────────────────────────
    try:
        result = subprocess.run(["free", "-m"], capture_output=True, text=True)
        parts = result.stdout.split("\n")[1].split()
        m["ram_total_mb"] = int(parts[1])
        m["ram_used_mb"]  = int(parts[2])
        m["ram_pct"]      = round(int(parts[2]) / int(parts[1]) * 100, 1)
    except Exception as e:
        log(f"Error RAM: {e}")

    # ── BD SIEG Política ──────────────────────────────────
    try:
        db = os.path.join(BASE_DIR, "data", "processed", "noticias.db")
        conn = sqlite3.connect(db)
        cur = conn.cursor()

        # Noticias últimas 24h
        cur.execute("SELECT COUNT(*) FROM noticias_norm WHERE created_at >= datetime('now', '-24 hours')")
        m["sieg_noticias_24h"] = cur.fetchone()[0]

        # Total noticias
        cur.execute("SELECT COUNT(*) FROM noticias_norm")
        m["sieg_noticias_total"] = cur.fetchone()[0]

        # Fuentes activas últimas 48h
        cur.execute("SELECT COUNT(DISTINCT source) FROM noticias_norm WHERE created_at >= datetime('now', '-48 hours')")
        m["sieg_fuentes_activas"] = cur.fetchone()[0]

        # Fecha último registro
        cur.execute("SELECT MAX(created_at) FROM noticias_norm")
        ultimo = cur.fetchone()[0]
        if ultimo:
            dt_ultimo = datetime.fromisoformat(ultimo)
            horas_desde_ultimo = (datetime.now() - dt_ultimo).total_seconds() / 3600
            m["sieg_horas_sin_datos"] = round(horas_desde_ultimo, 1)
            if horas_desde_ultimo > 10:
                alertas.append(f"⚠️ SIEG: sin datos nuevos hace {horas_desde_ultimo:.1f}h")

        conn.close()
    except Exception as e:
        log(f"Error BD SIEG: {e}")
        alertas.append(f"❌ Error acceso BD SIEG: {e}")

    # ── BD Narrative Radar ────────────────────────────────
    try:
        db_nr = os.path.join(NR_DIR, "data", "news.db")
        if os.path.exists(db_nr):
            conn = sqlite3.connect(db_nr)
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM news")
            m["nr_noticias_total"] = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM news WHERE date >= datetime('now', '-24 hours')")
            m["nr_noticias_24h"] = cur.fetchone()[0]

            # Detectar fechas futuras
            cur.execute("SELECT COUNT(*) FROM news WHERE date > datetime('now', '+1 day')")
            futuras = cur.fetchone()[0]
            m["nr_fechas_futuras"] = futuras
            if futuras > 0:
                alertas.append(f"⚠️ NR: {futuras} noticias con fecha futura detectadas")

            conn.close()
    except Exception as e:
        log(f"Error BD NR: {e}")

    # ── Pipeline SIEG — última ejecución ──────────────────
    try:
        log_path = os.path.join(BASE_DIR, "logs", "pipeline.log")
        if os.path.exists(log_path):
            with open(log_path, "r") as f:
                lines = f.readlines()
            for line in reversed(lines):
                if "Pipeline completado" in line or "completado" in line.lower():
                    ts_pipeline = line[:26]
                    try:
                        dt_pipe = datetime.fromisoformat(ts_pipeline.strip("[]"))
                        horas = (datetime.now() - dt_pipe).total_seconds() / 3600
                        m["pipeline_horas"] = round(horas, 1)
                        if horas > 9:
                            alertas.append(f"⚠️ Pipeline SIEG: última ejecución hace {horas:.1f}h")
                    except:
                        pass
                    break
    except Exception as e:
        log(f"Error pipeline check: {e}")

    # ── Espacio exports ───────────────────────────────────
    try:
        export_dir = os.path.join(BASE_DIR, "data", "export")
        total = sum(
            os.path.getsize(os.path.join(export_dir, f))
            for f in os.listdir(export_dir)
            if os.path.isfile(os.path.join(export_dir, f))
        )
        m["exports_mb"] = round(total / 1024 / 1024, 2)
    except:
        pass

    return m, alertas

def detectar_anomalias_adaptativas(m, umbrales):
    """Detecta anomalías usando umbrales aprendidos."""
    anomalias = []

    checks = {
        "disco_pct":           ("Disco", "%", "alto"),
        "ram_pct":             ("RAM", "%", "alto"),
        "sieg_horas_sin_datos":("SIEG sin datos", "h", "alto"),
        "sieg_fuentes_activas":("Fuentes activas SIEG", "", "bajo"),
        "sieg_noticias_24h":   ("Noticias SIEG 24h", "", "bajo"),
        "nr_noticias_24h":     ("Noticias NR 24h", "", "bajo"),
        "pipeline_horas":      ("Pipeline sin correr", "h", "alto"),
    }

    for clave, (nombre, unidad, tipo) in checks.items():
        if clave not in m or clave not in umbrales:
            continue
        val = m[clave]
        u   = umbrales[clave]
        if tipo == "alto" and val > u["max"] and u["std"] > 0:
            desv = (val - u["media"]) / u["std"]
            anomalias.append(
                f"📈 <b>{nombre}</b>: {val}{unidad} "
                f"(normal: {u['media']:.1f}±{u['std']:.1f}, +{desv:.1f}σ)"
            )
        elif tipo == "bajo" and val < u["min"] and u["std"] > 0:
            desv = (u["media"] - val) / u["std"]
            anomalias.append(
                f"📉 <b>{nombre}</b>: {val}{unidad} "
                f"(normal: {u['media']:.1f}±{u['std']:.1f}, -{desv:.1f}σ)"
            )

    return anomalias

def main():
    log("Iniciando diagnóstico")

    hist = cargar_historico()
    m, alertas_criticas = medir_metricas()

    # Guardar muestra
    hist["muestras"].append(m)
    if len(hist["muestras"]) > 200:
        hist["muestras"] = hist["muestras"][-200:]

    # Aprender umbrales
    umbrales = aprender_umbrales(hist)
    hist["umbrales"] = umbrales
    n_muestras = len(hist["muestras"])

    log(f"Métricas: disco={m.get('disco_pct','?')}% RAM={m.get('ram_pct','?')}% "
        f"SIEG_24h={m.get('sieg_noticias_24h','?')} NR_24h={m.get('nr_noticias_24h','?')}")
    log(f"Umbrales aprendidos: {len(umbrales)} métricas · {n_muestras} muestras históricas")

    # Detectar anomalías adaptativas
    anomalias_adapt = detectar_anomalias_adaptativas(m, umbrales)

    todas_alertas = alertas_criticas + anomalias_adapt

    if todas_alertas:
        hist["anomalias"].append({"ts": m["ts"], "alertas": todas_alertas})
        if len(hist["anomalias"]) > 100:
            hist["anomalias"] = hist["anomalias"][-100:]

        msg = (
            f"🔬 <b>SIEG — Auto-diagnóstico</b>\n"
            f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
            f"📊 Muestras históricas: {n_muestras}\n"
            f"{'─'*30}\n\n"
        )
        msg += "\n".join(todas_alertas)
        msg += (
            f"\n\n{'─'*30}\n"
            f"💾 Disco: {m.get('disco_pct','?')}% · "
            f"🧠 RAM: {m.get('ram_pct','?')}%\n"
            f"© 2026 M. Castillo"
        )
        send_telegram(msg)
        log(f"{len(todas_alertas)} alertas enviadas")
    else:
        log("Sistema OK — sin anomalías detectadas")

    guardar_historico(hist)
    log("Diagnóstico completado")

if __name__ == "__main__":
    main()
