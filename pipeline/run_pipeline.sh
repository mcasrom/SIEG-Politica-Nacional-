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
