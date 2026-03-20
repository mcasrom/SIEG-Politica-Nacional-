#!/usr/bin/env python3
"""
telegram_notify.py
SIEG – Centro OSINT · Política Nacional

Publica resumen diario automático en canal Telegram @sieg_politica.
Se integra en el pipeline tras cada ejecución.

Cron: ya incluido en run_pipeline.sh

Autor : M. Castillo · mybloggingnotes@gmail.com
© 2026 M. Castillo – Todos los derechos reservados
"""

import os
import json
import sqlite3
import requests
from datetime import datetime

BASE_DIR   = os.path.expanduser("~/SIEG-Politica-Nacional")
DB_PATH    = os.path.join(BASE_DIR, "data", "processed", "noticias.db")
CFG_PATH   = os.path.join(BASE_DIR, "config", "politica_config.json")
LOG_PATH   = os.path.join(BASE_DIR, "logs", "pipeline.log")

BOT_TOKEN  = "8789958560:AAGRB5opW11gL6m13cXwUAjJcr_bZN2Y9fM"
CHANNEL    = "@sieg_politica"
API_URL    = f"https://api.telegram.org/bot{BOT_TOKEN}"

def log(msg):
    ts = datetime.now().isoformat()
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] [TELEGRAM] {msg}\n")
    print(f"[TELEGRAM] {msg}")

def send_message(text, parse_mode="HTML"):
    r = requests.post(f"{API_URL}/sendMessage", json={
        "chat_id":    CHANNEL,
        "text":       text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True
    }, timeout=15)
    if r.status_code == 200:
        log("Mensaje enviado OK")
    else:
        log(f"Error {r.status_code}: {r.text}")
    return r.status_code == 200

def send_document(path, caption=""):
    with open(path, "rb") as f:
        r = requests.post(f"{API_URL}/sendDocument", data={
            "chat_id": CHANNEL,
            "caption": caption,
            "parse_mode": "HTML"
        }, files={"document": f}, timeout=30)
    if r.status_code == 200:
        log(f"Documento enviado: {os.path.basename(path)}")
    else:
        log(f"Error documento {r.status_code}: {r.text}")
    return r.status_code == 200

def build_mensaje(conn, cfg):
    import pandas as pd

    df = pd.read_sql_query("SELECT * FROM noticias_norm", conn)
    df["sent_score"] = df["sentiment_label"].map({"POS": 1, "NEU": 0, "NEG": -1})
    df["fecha"] = pd.to_datetime(df["created_at"], errors="coerce").dt.date

    hoy        = df["fecha"].max()
    df_hoy     = df[df["fecha"] == hoy]
    total      = len(df_hoy)
    sent_medio = df_hoy["sent_score"].mean()
    pct_neg    = (df_hoy["sentiment_label"] == "NEG").mean() * 100
    fuentes    = df_hoy["source"].nunique()

    # Sentimiento emoji
    if sent_medio > 0.15:
        sent_icon = "🟢"
    elif sent_medio < -0.15:
        sent_icon = "🔴"
    else:
        sent_icon = "🟡"

    # Top 3 partidos por volumen hoy
    top_partidos = df_hoy["partido"].value_counts().head(3)

    # Alertas críticas
    fechas = sorted(df["fecha"].unique())
    alertas = []
    if len(fechas) >= 2:
        anteriores = fechas[:-1]
        df_ant = df[df["fecha"].isin(anteriores)]
        for partido in df_hoy["partido"].unique():
            dh = df_hoy[df_hoy["partido"] == partido]
            da = df_ant[df_ant["partido"] == partido]
            if len(dh) < 3:
                continue
            pn_hoy = (dh["sentiment_label"] == "NEG").mean() * 100
            if len(da) > 0:
                pn_ant = da.groupby("fecha").apply(
                    lambda x: (x["sentiment_label"] == "NEG").mean() * 100,
                    include_groups=False
                ).mean()
                delta = pn_hoy - pn_ant
                if delta > 10:
                    alertas.append(f"🔴 <b>{partido}</b> +{delta:.1f}pp negatividad")

    # Narrativas del día
    narr_counts = {}
    for _, row in df_hoy.iterrows():
        if row.get("narrativas") and str(row["narrativas"]) not in ["ninguna", "nan"]:
            for n in str(row["narrativas"]).split(","):
                n = n.strip()
                if n:
                    narr_counts[n] = narr_counts.get(n, 0) + 1
    top_narr = sorted(narr_counts.items(), key=lambda x: -x[1])[:3]

    # Construir mensaje
    fecha_str = hoy.strftime("%d/%m/%Y") if hasattr(hoy, "strftime") else str(hoy)

    msg = f"""🛰️ <b>SIEG – Radar Político España</b>
📅 <b>{fecha_str}</b>

📊 <b>Resumen del día</b>
• Noticias analizadas: <b>{total:,}</b>
• Fuentes activas: <b>{fuentes}</b>
• Sentimiento medio: {sent_icon} <b>{sent_medio:+.2f}</b>
• Negatividad: <b>{pct_neg:.1f}%</b>

🏛️ <b>Partidos más activos</b>
"""
    for partido, n in top_partidos.items():
        msg += f"• {partido}: {n} noticias\n"

    if alertas:
        msg += "\n🚨 <b>Alertas</b>\n"
        for a in alertas[:3]:
            msg += f"{a}\n"

    if top_narr:
        msg += "\n🌀 <b>Narrativas activas</b>\n"
        for narr, cnt in top_narr:
            msg += f"• {narr}: {cnt} menciones\n"

    msg += f"""
📈 Dashboard: https://politica-nacional-osint.streamlit.app
© 2026 M. Castillo · <a href="mailto:mybloggingnotes@gmail.com">mybloggingnotes@gmail.com</a>"""

    return msg

def main():
    log("Iniciando notificación Telegram")

    conn = sqlite3.connect(DB_PATH)

    try:
        with open(CFG_PATH, encoding="utf-8") as f:
            cfg = json.load(f)

        msg = build_mensaje(conn, cfg)
        send_message(msg)

        # Adjuntar último PDF si existe
        import glob
        reports = sorted(glob.glob(
            os.path.join(BASE_DIR, "data", "reports", "*.pdf")
        ), reverse=True)
        if reports:
            send_document(reports[0], caption="📄 Informe completo del día")

    except Exception as e:
        log(f"ERROR: {e}")
        import traceback
        log(traceback.format_exc())
    finally:
        conn.close()

    log("Notificación completada")

if __name__ == "__main__":
    main()
