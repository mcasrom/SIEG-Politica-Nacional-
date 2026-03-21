#!/usr/bin/env python3
"""
spike_alerts.py
SIEG – Centro OSINT · Política Nacional

Detecta spikes de narrativas, negatividad y volumen
y envía alertas al canal Telegram @sieg_politica.

Ejecutar tras cada pipeline:
- Añadir al final de run_pipeline.sh

Cron sugerido (cada 7h tras pipeline):
Ya integrado en run_pipeline.sh

Autor : M. Castillo · mybloggingnotes@gmail.com
© 2026 M. Castillo
"""

import os
import sqlite3
import requests
from datetime import datetime, timedelta

BASE_DIR   = os.path.expanduser("~/SIEG-Politica-Nacional")
DB_PATH    = os.path.join(BASE_DIR, "data", "processed", "noticias.db")
LOG_PATH   = os.path.join(BASE_DIR, "logs", "pipeline.log")
BOT_TOKEN  = "8789958560:AAGRB5opW11gL6m13cXwUAjJcr_bZN2Y9fM"
CHANNEL    = "@sieg_politica"
API_URL    = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Umbrales
SPIKE_NARRATIVA_PCT  = 150   # % sobre media anterior para considerar spike
SPIKE_NEGATIVIDAD_PP = 15    # puntos porcentuales sobre media anterior
SPIKE_VOLUMEN_PCT    = 200   # % sobre media anterior para volumen

def log(msg):
    ts = datetime.now().isoformat()
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] [SPIKE] {msg}\n")
    print(f"[SPIKE] {msg}")

def send_alert(text):
    try:
        r = requests.post(f"{API_URL}/sendMessage", json={
            "chat_id":    CHANNEL,
            "text":       text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }, timeout=15)
        if r.status_code == 200:
            log("Alerta enviada OK")
        else:
            log(f"Error Telegram {r.status_code}")
    except Exception as e:
        log(f"Error enviando alerta: {e}")

def main():
    log("Iniciando detección de spikes")
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    hoy       = datetime.now().date()
    ayer      = hoy - timedelta(days=1)
    hace3dias = hoy - timedelta(days=3)

    alertas = []

    # ── 1. Spike de narrativas ────────────────────────────
    # Narrativas de hoy
    cur.execute("""
        SELECT trim(value) as narr, COUNT(*) as total
        FROM noticias_norm,
             json_each('["' || replace(replace(narrativas, ',', '","'), ' ', '') || '"]')
        WHERE DATE(created_at) = ? AND narrativas != 'ninguna' AND narrativas IS NOT NULL
        GROUP BY narr
        ORDER BY total DESC
    """, (str(hoy),))
    narr_hoy = {r[0]: r[1] for r in cur.fetchall() if r[0]}

    # Media narrativas días anteriores
    cur.execute("""
        SELECT trim(value) as narr, COUNT(*) * 1.0 / COUNT(DISTINCT DATE(created_at)) as media_dia
        FROM noticias_norm,
             json_each('["' || replace(replace(narrativas, ',', '","'), ' ', '') || '"]')
        WHERE DATE(created_at) BETWEEN ? AND ?
        AND narrativas != 'ninguna' AND narrativas IS NOT NULL
        GROUP BY narr
    """, (str(hace3dias), str(ayer)))
    narr_media = {r[0]: r[1] for r in cur.fetchall() if r[0]}

    for narr, cnt_hoy in narr_hoy.items():
        if narr in narr_media and narr_media[narr] > 0:
            pct = (cnt_hoy / narr_media[narr]) * 100
            if pct >= SPIKE_NARRATIVA_PCT and cnt_hoy >= 5:
                alertas.append(
                    f"🔺 <b>SPIKE NARRATIVA:</b> <code>{narr}</code>\n"
                    f"   Hoy: {cnt_hoy} menciones vs media: {narr_media[narr]:.1f}/día "
                    f"(+{pct-100:.0f}%)"
                )
        elif narr not in narr_media and cnt_hoy >= 10:
            alertas.append(
                f"🆕 <b>NARRATIVA NUEVA:</b> <code>{narr}</code>\n"
                f"   {cnt_hoy} menciones hoy — sin histórico previo"
            )

    # ── 2. Spike de negatividad por partido ──────────────
    cur.execute("""
        SELECT partido,
               SUM(CASE WHEN sentiment_label='NEG' THEN 1.0 ELSE 0 END) / COUNT(*) * 100 as pct_neg,
               COUNT(*) as total
        FROM noticias_norm
        WHERE DATE(created_at) = ? AND partido IS NOT NULL
        GROUP BY partido
        HAVING total >= 5
        ORDER BY pct_neg DESC
    """, (str(hoy),))
    neg_hoy = {r[0]: (r[1], r[2]) for r in cur.fetchall()}

    cur.execute("""
        SELECT partido,
               SUM(CASE WHEN sentiment_label='NEG' THEN 1.0 ELSE 0 END) / COUNT(*) * 100 as pct_neg
        FROM noticias_norm
        WHERE DATE(created_at) BETWEEN ? AND ? AND partido IS NOT NULL
        GROUP BY partido
    """, (str(hace3dias), str(ayer)))
    neg_media = {r[0]: r[1] for r in cur.fetchall()}

    for partido, (pct_hoy, total) in neg_hoy.items():
        if partido in neg_media:
            delta = pct_hoy - neg_media[partido]
            if delta >= SPIKE_NEGATIVIDAD_PP:
                alertas.append(
                    f"🔴 <b>SPIKE NEGATIVIDAD:</b> {partido}\n"
                    f"   NEG hoy: {pct_hoy:.1f}% vs media: {neg_media[partido]:.1f}% "
                    f"(+{delta:.1f}pp) · {total} noticias"
                )

    # ── 3. Spike de volumen total ─────────────────────────
    cur.execute("""
        SELECT COUNT(*) FROM noticias_norm WHERE DATE(created_at) = ?
    """, (str(hoy),))
    vol_hoy = cur.fetchone()[0]

    cur.execute("""
        SELECT AVG(daily_count) FROM (
            SELECT COUNT(*) as daily_count
            FROM noticias_norm
            WHERE DATE(created_at) BETWEEN ? AND ?
            GROUP BY DATE(created_at)
        )
    """, (str(hace3dias), str(ayer)))
    vol_media = cur.fetchone()[0] or 0

    if vol_media > 0:
        vol_pct = (vol_hoy / vol_media) * 100
        if vol_pct >= SPIKE_VOLUMEN_PCT:
            alertas.append(
                f"📈 <b>SPIKE VOLUMEN:</b> {vol_hoy} noticias hoy\n"
                f"   Media anterior: {vol_media:.0f}/día (+{vol_pct-100:.0f}%)"
            )

    conn.close()

    # ── Enviar alertas ────────────────────────────────────
    if alertas:
        msg = (
            f"🚨 <b>SIEG — Alertas de Spike</b>\n"
            f"📅 {hoy.strftime('%d/%m/%Y')}\n"
            f"{'─'*30}\n\n"
        )
        msg += "\n\n".join(alertas)
        msg += (
            f"\n\n{'─'*30}\n"
            f"📊 <a href='https://politica-nacional-osint.streamlit.app'>Ver dashboard</a> · "
            f"© 2026 M. Castillo"
        )
        send_alert(msg)
        log(f"{len(alertas)} alertas enviadas")
    else:
        log("Sin spikes detectados")

if __name__ == "__main__":
    main()
