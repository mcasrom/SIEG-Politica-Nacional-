#!/bin/bash

echo "=== Ejecutando pipeline SIEG ==="

BASE="/home/dietpi/SIEG-Politica-Nacional"
VENV="$BASE/venv/bin/activate"

# Activar entorno virtual
source $VENV

# 1. Ingesta de RSS
python3 $BASE/scripts/fetch_rss.py

# 2. Procesamiento NLP
python3 $BASE/scripts/process_nlp.py

# 3. Normalización de partidos
python3 $BASE/scripts/normalize_partidos.py

# 4. Extensión de normalización
python3 $BASE/scripts/normalize_and_extend_parties.py

# 4.5 
python3 $BASE/scripts/classify_topics.py

python3 $BASE/scripts/detect_narrativas.py


# 5. Territorios básicos
python3 $BASE/scripts/detect_territorios.py

# 6. Territorios por contexto
python3 $BASE/scripts/detect_territorios_contexto.py

# 7. Coocurrencias
python3 $BASE/scripts/detect_coocurrencias.py

# 7.5

python3 $BASE/scripts/detect_tendencias.py


# 8. Limpieza de retención
python3 $BASE/scripts/retention_cleanup.py

echo "=== Pipeline completado ==="
