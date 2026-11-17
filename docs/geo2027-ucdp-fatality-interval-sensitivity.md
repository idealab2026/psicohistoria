# GEO2027 — Sensibilidad del resultado al intervalo bajo/central/alto de UCDP

**Extensión metodológica, 17/11/2026. No hay resultados observados de 2027.**

## Pregunta

La predicción prospectiva GEO2027 está definida desde la primera emisión como **probabilidad de que `sb_total_deaths_best >= 25`** en 2027, en cada uno de los 196 países (GWNO) congelados. UCDP ofrece también las estimaciones `sb_total_deaths_low` y `sb_total_deaths_high`. Su manual oficial 26.1 (pp. 3–4) permite distinguir los tres recuentos; **no son intervalos de confianza** y no se deben interpretar como probabilidad de que el número real esté dentro de sus extremos.

Referencia oficial: [UCDP OrganizedViolenceCY Codebook 26.1](https://ucdp.uu.se/downloads/organizedviolencecy/UCDP_OrganizedViolenceCY_Codebook_261.pdf). Los nombres de variables para la edición actual admiten la forma sin sufijo y versiones anteriores/alternativas con sufijo `_cy`.

Este estudio añade una **evaluación secundaria de sensibilidad de la etiqueta a la medición**, no un modelo nuevo ni una nueva definición de acierto. La evaluación primaria registrada antes de disponer de los datos mantiene `best >= 25`.

## Procedimiento

Se compara exclusivamente la pareja registrada antes de los resultados:

`D = Brier(global-only matched α1) − Brier(LOG1P original)`

usando las 196 probabilidades originales publicadas, inalteradas. Para cada país y cada año objetivo se requieren tres recuentos numéricos **explícitos** `low <= best <= high`; nunca se rellena una fila ausente con cero.

- **Inactivo bajo ambas estimaciones:** `high < 25`. Su etiqueta no cambia dentro del escenario bajo/alto.
- **Activo bajo ambas estimaciones:** `low >= 25`.
- **Umbral ambiguo entre estimaciones:** `low < 25 <= high`. Puede cambiar el indicador según el estimador seleccionado; esto **no** supone que cada estimación sea una realización aleatoria equiprobable.

Se calculan los Brier emparejados usando coherentemente `low`, `best` y `high` en los 196 países, siempre en el mismo denominador 196. Además, los extremos matemáticos agudos se obtienen sumando, para cada país ambiguo, el mínimo y máximo de `(p−y)^2−(q−y)^2`, con `y∈{0,1}`; los no ambiguos conservan etiqueta fija. Son **cotas algebraicas de sensibilidad**, no bandas de predicción, intervalos estadísticos de confianza, efectos causales ni conjuntos de escenarios necesariamente alcanzables por la misma configuración real de conflictos.

Si `low` y `high` atraviesan 25 para cero países, las cotas colapsan a la puntuación con `best`. Si divergen, se podrá comprobar si la conclusión de mejor Brier es sensible a la forma de estimar fallecidos. El resultado no autoriza a seleccionar retrospectivamente la definición de etiqueta favorable.

## Puerta de integridad, fuente y tiempo

`scripts/audit_geo2027_fatality_intervals.py` **sin fuente** devuelve únicamente el estado `NOT_READY_NO_VERIFIED_OFFICIAL_2027_RELEASE`, sin Brier. Las pruebas automatizadas usan **exclusivamente fuentes sintéticas** y verifican ausencia de fila, duplicidad, números negativos/decimales, relaciones `low>best` o `best>high`, las dos variantes de nombres, ZIP y filas posteriores a 2027.

Cuando exista la primera edición oficial completa de 2027, a partir de 2028, el script aceptará `--source archivo.csv/zip --provenance revision.json`. Reutiliza íntegramente `resolve_geo2027_first_complete_official.py`: revisión humana de procedencia y prioridad de edición, hash SHA-256, 196 países, fecha posterior a 2027, puntuación principal de cinco modelos e identidad Brier preemitida. **Una ficha humana no demuestra criptográficamente la autenticidad ni que sea la primera edición completa.** Además exige `low <= best <= high` en las 196 filas y comprueba que la nueva puntuación `best` es **idéntica** a la primaria.

No publica una evaluación nueva por defecto ni altera una sola predicción del GEO original, LOG1P, global-only o las 15 alertas congeladas.

## Estado comprobable

- **Predicciones nuevas:** 0
- **Resultados oficiales 2027:** 0/196
- **Capacidad implementada:** parser y prueba de sensibilidad por estimaciones de muertes; cálculo futuro condicionado a edición oficial completa
- **Evidencia presente:** metodología auditada mediante casos sintéticos; los recuentos reales de países con umbral ambiguo en 2027 son **desconocidos**
- **Limitaciones:** muertes codificadas no equivalen a toda la violencia real; países geopolíticamente dependientes; `low/high` no son bandas probabilísticas; no existe todavía validación prospectiva de habilidad de ningún modelo

El proyecto y las referencias se mantienen exclusivamente en la identidad institucional de IDEA LAB.
