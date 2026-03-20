# WATCH OUT — Issues conocidos y pendientes

## Fuentes débiles (bajo volumen político)
Las siguientes fuentes RSS están activas pero generan muy pocas noticias
con menciones a partidos políticos nacionales. No están caídas — su cobertura
política simplemente es baja. Considerar marcarlas como `"type": "local_low"`
en `config/feeds_rss.json` y excluirlas de las alertas de auditoría:

- La Provincia Las Palmas
- La Opinión A Coruña
- La Nueva España / La Nueva España Asturias
- Información Alicante
- Faro de Vigo
- El Día Tenerife
- Diario de Mallorca
- Diari de Girona

**Acción pendiente:** añadir campo `"low_coverage": true` en feeds_rss.json
y filtrar estas fuentes en el cálculo de fuentes caídas del panel de auditoría.

## Alerta fuentes caídas
Umbral ajustado a 48h (antes 24h) para reducir falsos positivos.
Revisar si sigue siendo ruidoso tras acumular más días de datos.

## BD en Streamlit Cloud
Los datos en Streamlit Cloud son CSV exportados desde el Odroid.
Se actualizan con cada ejecución del pipeline (cada 7h via cron).
Máximo 7 días de histórico en el export para no inflar el repo.

## Token GitHub en remote
El token ghp_ está embebido en el remote URL del repo local.
Rotar el token en GitHub si se compromete o expira.
Actualizar con: git remote set-url origin https://mcasrom:TOKEN@github.com/...

## Partidos con muestra baja
BNG (2), SALF (2), MÁS MADRID (7) tienen muy pocas noticias.
La valoración mediática para estos partidos no es estadísticamente fiable.
Umbral mínimo de fiabilidad: 10 noticias (ya marcado en dashboard).
