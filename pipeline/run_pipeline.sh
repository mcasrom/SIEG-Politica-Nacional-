#!/bin/bash
# =============================================================
# run_pipeline.sh — SIEG Política Nacional
# Autor : M. Castillo · mybloggingnotes@gmail.com
# © 2026 M. Castillo
# =============================================================

source /home/dietpi/SIEG-Politica-Nacional/venv/bin/activate
BASE="/home/dietpi/SIEG-Politica-Nacional"
LOG="$BASE/logs/pipeline.log"
TS=$(date '+%Y-%m-%d %H:%M:%S')

echo "" >> "$LOG"
echo "======================================" >> "$LOG"
echo "[$TS] Pipeline iniciado" >> "$LOG"
echo "======================================" >> "$LOG"

run_step() {
    local name="$1"
    local script="$2"
    if [ -f "$script" ]; then
        echo "[$name] Ejecutando..." >> "$LOG"
        python "$script" >> "$LOG" 2>&1
        if [ $? -eq 0 ]; then
            echo "[$name] OK" >> "$LOG"
        else
            echo "[$name] ERROR — ver log" >> "$LOG"
        fi
    else
        echo "[$name] SKIP — no encontrado: $script" >> "$LOG"
    fi
}

# 1. Ingesta RSS
run_step "fetch_rss"       "$BASE/scripts/fetch_rss.py"

# 2. Análisis NLP + sentimiento
run_step "process_nlp"     "$BASE/scripts/process_nlp.py"

# 3. Normalización de partidos
run_step "norm_partidos"   "$BASE/scripts/normalize_partidos.py"

# 4. Extensión de partidos
run_step "norm_extend"     "$BASE/scripts/normalize_and_extend_parties.py"

# 5. Clasificación de temas
run_step "classify_topics" "$BASE/scripts/classify_topics.py"

# 6. Detección de narrativas
run_step "narrativas"      "$BASE/scripts/detect_narrativas.py"

# 7. Tendencias diarias
run_step "tendencias"      "$BASE/scripts/detect_tendencias.py"

# 8. Territorios básicos
run_step "territorios"     "$BASE/scripts/detect_territorios.py"

# 9. Territorios por contexto
run_step "terr_contexto"   "$BASE/scripts/detect_territorios_contexto.py"

# 10. Coocurrencias
run_step "coocurrencias"   "$BASE/scripts/detect_coocurrencias.py"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Pipeline completado" >> "$LOG"

# Copiar ultimo PDF al repo para Streamlit Cloud
echo "[pdf_export] Copiando PDF al repo..." >> "$LOG"
_pdf=$(ls -t $BASE/data/reports/*.pdf 2>/dev/null | head -1)
if [ -n "$_pdf" ]; then
    cp "$_pdf" "$BASE/data/export/ultimo_informe.pdf"
    echo "[pdf_export] PDF copiado: " >> ""
fi

# Export CSV y push a GitHub (para Streamlit Cloud)
echo "[export] Exportando CSV..." >> "$LOG"
source /home/dietpi/SIEG-Politica-Nacional/venv/bin/activate
python3 - << 'PYEOF' >> "$LOG" 2>&1
import sqlite3, pandas as pd, os
BASE = os.path.expanduser("~/SIEG-Politica-Nacional")
DB   = os.path.join(BASE, "data", "processed", "noticias.db")
OUT  = os.path.join(BASE, "data", "export")
os.makedirs(OUT, exist_ok=True)
conn = sqlite3.connect(DB)
pd.read_sql_query("SELECT * FROM noticias_norm WHERE DATE(created_at) >= DATE('now', '-7 days')", conn).to_csv(f"{OUT}/noticias_norm.csv", index=False)
pd.read_sql_query("SELECT * FROM tendencias_diarias", conn).to_csv(f"{OUT}/tendencias_diarias.csv", index=False)
conn.close()
print("CSV exportados OK")
PYEOF

# Git push
cd /home/dietpi/SIEG-Politica-Nacional
git add data/export/
git commit -m "data: update export $(date '+%Y-%m-%d %H:%M')" >> "$LOG" 2>&1
git push origin main >> "$LOG" 2>&1
echo "[export] Push completado" >> "$LOG"

# Generar informe PDF diario
echo [pdf] Generando informe PDF... >> $LOG
python3 $BASE/scripts/generate_report_pdf.py >> $LOG 2>&1
echo [pdf] Informe generado >> $LOG

# Notificación Telegram
echo [telegram] Enviando resumen al canal... >> $LOG
python3 $BASE/scripts/telegram_notify.py >> $LOG 2>&1
echo [telegram] Notificación completada >> $LOG

# Alertas de spike
echo [spike] Detectando spikes... >> $LOG
python3 $BASE/scripts/spike_alerts.py >> $LOG 2>&1
echo [spike] Completado >> $LOG
