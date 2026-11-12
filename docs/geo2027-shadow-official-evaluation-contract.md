# GEO-2027 — Evaluador futuro del shadow calibrado frente al original

**12 de noviembre de 2026.** Contrato de evaluación prospectiva, no evaluación real: **ningún resultado de 2027 está observado**.

La primera emisión pública del shadow de 196 países, con su propio SHA-256 y sello temporal público de GitHub, está fijada en `data/forecast-2027-geo-shadow-manifest.json`. El original GEO-2027 y sus 15 alertas se conservan sin cambios.

## Contrato primario irreversible

Una vez disponible la **primera edición completa oficial de UCDP OrganizedViolenceCY que incluya 2027**, se evaluará sobre el mismo conjunto de 196 países ya emitidos:

\[
\Delta Brier =
\frac{1}{196}\sum_{i=1}^{196}(p_{shadow,i}-y_i)^2
-
\frac{1}{196}\sum_{i=1}^{196}(p_{original,i}-y_i)^2.
\]

- **Negativo:** favorece al modelo shadow.
- **Positivo:** favorece al modelo original.
- **Cero:** misma pérdida de Brier.
- **Métrica secundaria:** diferencia emparejada de log-loss (shadow menos original).
- **Diagnóstico adicional, no sustituto:** las mismas pérdidas por estado conocido en 2025 (162 países inicialmente inactivos y 34 activos), y número de países con mejora/empeoramiento individual.

Los valores publicados se derivarán de las probabilidades **ya emitidas** (no se reajustarán ni ordenarán países según los resultados). Si falta **un solo país de los 196**, el informe marcará `PARTIAL_OFFICIAL_2027_COVERAGE_NO_SCORES` y dejará sin calcular **todas** las pérdidas, incluso las de subgrupos aparentemente completos. No se rellenará con 0 un país ausente o una cifra de muertes sin informar.

## Procedencia oficial y certificación

`scripts/evaluate_geo2027_calibrated_shadow_official.py` obliga a suministrar explícitamente los bytes de un ZIP de la fuente oficial, el SHA-256 esperado, la URL de UCDP y una fecha posterior al 31/12/2027. Reutiliza las comprobaciones de fuente del evaluador original y las de la cohorte de alertas: dominios institucionales, estructura CSV, campo de muertes por violencia estatal, IDs, año, duplicados, valores inválidos y etiquetas ausentes.

**La URL y la fecha declaradas no constituyen prueba independiente** de que sea la primera edición completa de UCDP 2027. Por ello, aun con 196 etiquetas la salida conserva siempre `FULL_COVERAGE_CANDIDATE_STILL_UNCERTIFIED`, con `source_first_complete_release_independently_certified=false` y `prospective_skill_independently_certified=false`.

El informe no escribe nada en el vector emitido original ni en el vector shadow. No publica puntuaciones ni etiquetas individuales en el resumen comparativo. Un script separado habrá de auditar oficialmente las fechas y las revisiones antes de cualquier certificación.

## Interpretación científica y límites

Esta es una comparación **realmente prospectiva respecto al objetivo 2027**, pero el shadow se seleccionó **después de examinar resultados históricos 2020–2025**. Por eso, una mejora futura en Brier no convertiría retrospectivamente su selección en confirmación independiente. Las pérdidas individuales están correlacionadas por shocks regionales y globales; no se construirán p-valores con la falsa premisa de 196 países IID.

Las pruebas de integración usan **etiquetas 2027 totalmente sintéticas**, tanto una muestra donde el shadow mejora como otra en la que empeora, más pruebas de ausencia de una etiqueta, IDs extra, modificaciones del vector original y etiquetas no binarias. No se ha generado ni se utilizará un dato futuro falso como si fuera una observación real.
