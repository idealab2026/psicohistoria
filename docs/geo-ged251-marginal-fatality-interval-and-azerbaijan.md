# PSICOHISTORIA · Intervalos de fallecidos GED25.1 y revisión de Azerbaiyán 2021

**Diseño cerrado el 19/11/2026 antes de examinar los límites low/high de los 118 eventos.** Se continúa desde la [PR #142](geo-ged251-togo2022-pivotal-source-genealogy.md), que identificó una sensibilidad matemática importante en Togo 2022: al reemplazar best=23 por low=8 en una única fila, el total del país pasaría de 34 a 19.

## Pregunta

¿En cuántos de los **14 países-año previamente seleccionados** con best estatal entre 15 y 35 fallecidos puede cambiar la clasificación binaria `≥25` cuando se consideran **las propias estimaciones low, best y high de UCDP GED25.1**? ¿Cuántos dependen exclusivamente de una fila de estimación incierta? Esta pregunta distingue **incertidumbre de medición publicada por la fuente** de errores reales de codificación o duplicación documental.

### Selección fijada, sin dependencia de low/high

- Población: **los mismos 14 GWNO-año de 2021 y 2022**, exactamente **118 filas de violencia tipo 1**, de la banda best `15..35` preregistrada en la [PR #137](geo-ged251-near25-countryyear-census.md) y verificada después en la [PR #141](geo-ged251-near25-source-publication-lag-census.md).
- ZIP oficial UCDP GED25.1, SHA-256 `e256f1fb20a579d8b2f910e5bae212f486d3002adaa2e4359ace740c737da05d`. Reproducir los **IDs originales** de cada país-año y el total best antes de calcular intervalos.
- Para cada país-año, sumar `low`, `best`, `high` de todas las filas de violencia estatal tipo 1, **incluidas las de best=0, las no geocodificables y las que no tienen fecha de publicación**. Exigir `low <= best <= high` individualmente.
- Clasificación: *negativo bajo las tres estimaciones* (`high <25`), *positivo bajo las tres* (`low >=25`) e *indeterminado entre límites* (`low <25<=high`). Se registran por separado desacuerdos best-vs-low y best-vs-high.
- Control adicional: variar el `best` de **una fila cada vez** a su `low` o `high`, dejando en best las demás, y contar país-años en que ese reemplazo hipotético mueve la etiqueta. **No seleccionar los países tras ver estos resultados.**
- No cuantificar errores globales de UCDP ni precisión de GEO a partir de la cohorte condicional a best. **La suma de intervalos de fuentes no es un intervalo probabilístico conjunto**. Es una envolvente aritmética de escenarios extremos que pueden estar correlacionados, resultar incompatibles documentalmente o no reflejar incertidumbre real conjunta.

### Control de fecha previamente identificado: Azerbaiyán

GED **427299**, GWNO **373**, evento estatal con best=1 de fecha exacta **17/06/2021** y **una cita bibliográfica fechada el 06/06/2021**. Se fija como control adicional antes de consultar el título y la procedencia del documento original: obtener de GED25.1 el titular, emisor, fecha, actores, lugar, díada y desglose low/best/high, conservando una huella SHA-256 bibliográfica. **No decidir que la fecha del hecho es falsa** por una publicación anterior sin comprobar si esa noticia trata de un episodio distinto o de contexto previo.

El año Azerbaiyán 2021 consta con best=30 en la cohorte anterior; eliminar hipotéticamente el registro de una muerte no cruza 25, por lo que la prioridad de este caso es documental, **no** de estabilidad individual de etiqueta.

## Límites y reproducibilidad

El informe estructurado se congelará en [JSON](../data/geo-ged251-marginal-low-best-high-2021-22.json) tras la primera ejecución SHA-verificada, y CI comprobará luego coincidencia exacta.

- `python3 -B -m unittest discover -s scripts -p 'test_audit_geo_ged251_marginal_fatality_interval.py' -v`
- `python3 -B scripts/audit_geo_ged251_marginal_fatality_interval.py --check-report`
- `python3 -B scripts/audit_public.py`

**Regla de interpretación:** los límites low/high provienen de una edición **retrospectiva de 2025**, por tanto no son datos as-of históricos para entrenar predicciones retrospectivas sin corte de fuente. No se cambia ningún registro histórico ni las probabilidades prospectivas GEO2027/GEO2028. No se afirma una mejora de Brier ni una habilidad predictiva nueva.
