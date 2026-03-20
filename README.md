# SIEG – Centro OSINT · Política Nacional

> **Sistema de Inteligencia y Evaluación Geopolítica**  
> Vigilancia narrativa automatizada · España · Política Nacional

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://fake-news-narrative.streamlit.app)

---

## ¿Qué es este proyecto?

**SIEG – Centro OSINT Política Nacional** es una plataforma de vigilancia narrativa automatizada que monitoriza en tiempo real la cobertura mediática de los principales partidos políticos españoles a través de fuentes RSS de medios nacionales, autonómicos y locales.

El sistema aplica análisis de sentimiento, detección de narrativas políticas y clasificación temática automática, generando un dashboard interactivo actualizado cada 7 horas.

**Este proyecto NO es** una herramienta de propaganda ni un sistema determinista. Los indicadores son estadísticos y aproximados, orientados a la detección temprana de tendencias y cambios en el discurso mediático.

---

## Funcionalidades

| Panel | Descripción |
|-------|-------------|
| 📊 Análisis General | KPIs globales, alertas de negatividad, valoración mediática de líderes, cobertura por fuente y territorio |
| 📈 Tendencias & Narrativas | Evolución temporal de temas y narrativas, ranking diario, alertas de picos |
| 🗺️ Tendencias por Territorio | Análisis geográfico por comunidad autónoma |
| 🧭 Inteligencia Narrativa | Análisis profundo por partido: KPIs, rotación histórica, mapa de calor, posicionamiento inferido |
| 📖 Guía de uso | Documentación completa del sistema |

---

## Arquitectura

```
RSS Feeds (medios nacionales, autonómicos, locales, partidos)
      │
      ▼
fetch_rss.py              ← Descarga y normaliza noticias
      │
      ▼
process_nlp.py            ← Análisis de sentimiento (TextBlob)
      │
      ▼
normalize_and_extend_parties.py  ← Asigna partido detectado
      │
      ▼
classify_topics.py        ← Clasificación temática
detect_narrativas.py      ← Detección de narrativas políticas
detect_tendencias.py      ← Cálculo de tendencias diarias
detect_territorios.py     ← Asignación territorial
      │
      ▼
noticias.db (SQLite)      ← Base de datos local · retención 30 días
      │
      ▼
app_dashboard.py          ← Dashboard Streamlit
```

**Infraestructura:** Odroid C2 · DietPi Linux · 1GB RAM  
**Pipeline:** cada 7 horas via cron  
**Deduplicación:** hash MD5 por `source + title + partido + published`  
**Retención:** 30 días activos (optimizado para hardware de bajo consumo)

---

## Estructura del repositorio

```
SIEG-Politica-Nacional/
├── config/
│   ├── feeds_rss.json          ← Fuentes RSS con tipo de medio
│   └── politica_config.json    ← ⚠️ CONFIGURACIÓN PRINCIPAL (ver abajo)
├── dashboard/
│   └── app_dashboard.py        ← Dashboard Streamlit
├── scripts/
│   ├── fetch_rss.py
│   ├── process_nlp.py
│   ├── normalize_partidos.py
│   ├── normalize_and_extend_parties.py
│   ├── classify_topics.py
│   ├── detect_narrativas.py
│   ├── detect_tendencias.py
│   ├── detect_territorios.py
│   ├── detect_territorios_contexto.py
│   ├── detect_coocurrencias.py
│   └── patch_hash_retention.py ← Limpieza semanal de BD
├── pipeline/
│   └── run_pipeline.sh         ← Script principal del pipeline
├── data/
│   ├── raw/                    ← JSONs de ingesta RSS (temporales)
│   └── processed/
│       └── noticias.db         ← Base de datos SQLite (no en repo)
└── logs/
    └── pipeline.log
```

---

## ⚠️ Configuración: actualizar líderes y partidos

**Todos los datos configurables están centralizados en un único archivo JSON:**

```
config/politica_config.json
```

Este archivo contiene — sin tocar ningún script Python:

### Cambiar un líder de partido

```json
"lideres": {
    "PP": {
        "lider": "Alberto Núñez Feijóo",
        "posicion": "Oposición",
        "ideologia": "Centro-derecha"
    }
}
```

Editar directamente y guardar. El dashboard lo carga en cada ejecución.

### Añadir un nuevo partido

```json
"partidos": {
    "NUEVO_PARTIDO": ["keyword1", "nombre líder", "alias"]
}
```

Y añadir su entrada en `"lideres"` con `lider`, `posicion` e `ideologia`.

### Añadir una nueva narrativa

```json
"narrativas": {
    "nueva_narrativa": ["keyword1", "keyword2", "expresión clave"]
},
"narrativas_perfil": {
    "nueva_narrativa": {
        "color": "#hexcolor",
        "desc": "Descripción del marco narrativo"
    }
}
```

### Añadir un tema de clasificación

```json
"temas": {
    "nuevo_tema": ["keyword1", "keyword2"]
}
```

---

## Instalación local

```bash
git clone https://github.com/TU_USUARIO/SIEG-Politica-Nacional.git
cd SIEG-Politica-Nacional

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Ejecutar pipeline inicial
bash pipeline/run_pipeline.sh

# Lanzar dashboard
streamlit run dashboard/app_dashboard.py
```

---

## Mantenimiento

**Limpieza y deduplicación de BD (recomendado semanalmente):**

```bash
source venv/bin/activate
python3 scripts/patch_hash_retention.py
```

**Añadir al cron (domingos 03:00):**

```bash
0 3 * * 0 cd ~/SIEG-Politica-Nacional && source venv/bin/activate && python3 scripts/patch_hash_retention.py >> logs/retention.log 2>&1
```

**Verificar estado de la BD:**

```bash
sqlite3 data/processed/noticias.db "
SELECT COUNT(*) as total,
       COUNT(DISTINCT hash_id) as unicos,
       MIN(DATE(created_at)) as desde,
       MAX(DATE(created_at)) as hasta
FROM noticias_norm;"
```

---

## Fuentes monitorizadas

- **Nacionales:** El País, El Mundo, ABC, La Vanguardia, El Confidencial, elDiario.es, El Español, Público, 20 Minutos, Infolibre
- **Agencias:** Europa Press, EFE
- **Regionales:** Diario Vasco, El Correo, La Voz de Galicia, Ara, El Periódico, Heraldo de Aragón, Hoy Extremadura y otros
- **Locales:** Diario de Sevilla, Ideal Granada, La Nueva España, Diario de Mallorca, La Provincia y otros
- **Partidos:** PSOE, PP, VOX, SUMAR, Podemos, ERC, Junts, PNV, EH Bildu
- **Economía:** Cinco Días, Expansión, El Economista
- **Internacional:** BBC Mundo, France24 ES

Lista completa y editable en `config/feeds_rss.json`.

---

## Limitaciones conocidas

- El análisis de sentimiento léxico (TextBlob) tiene limitaciones con el español político — tiende a clasificar como neutras noticias que un humano percibiría como negativas. RoBERTa-ES ofrece mayor precisión.
- La detección de partidos por keywords puede producir falsos positivos en contextos internacionales.
- Los datos territoriales están disponibles para un subconjunto de noticias.
- La retención de 30 días limita el análisis histórico largo. Exportar datos antes de la rotación para estudios comparativos.

---

## Autor y licencia

**© 2026 M. Castillo · Todos los derechos reservados**  
Contacto: [mybloggingnotes@gmail.com](mailto:mybloggingnotes@gmail.com)  

Uso personal e investigación. No se autoriza la redistribución comercial sin permiso expreso del autor.
