# GEO-2027 — Protocolo de alertas prospectivas por transición

**11 de noviembre de 2026.** Instrumento secundario, derivado únicamente de las **196 probabilidades originales GEO-2027 ya emitidas**. No genera un modelo nuevo y no altera el pronóstico principal.

## Preguntas a evaluar en 2027

Dos objetivos **separados**, ambos para el año natural **2027**, con estado de origen conocido **2025** (horizonte dos años):

1. **Entradas**: entre los **162 países** sin indicador activo en 2025, seleccionar exactamente los **10** de mayor `p_model` emitida para 2027. Etiqueta positiva si la primera edición oficial completa UCDP OrganizedViolenceCY del año 2027 registra `sb_total_deaths_best >= 25`.
2. **Resoluciones de umbral**: entre los **34 países** con indicador activo en 2025, seleccionar exactamente los **5** de mayor `1-p_model`. Etiqueta positiva si la primera edición oficial completa 2027 registra `sb_total_deaths_best < 25`.

**Una entrada no equivale a un conflicto nuevo `newconf`; una resolución no implica acuerdo de paz, ausencia total de violencia ni fin político de la guerra.** El criterio es el paso de un lado al otro del umbral de la base UCDP.

## Conjunto y predicciones congelados

Fuente canónica: `data/forecast-2027-ucdp261.json`, emitida públicamente el **10 de noviembre de 2026**, hash SHA-256:

`5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5`.

El generador `scripts/prepare_geo2027_transition_alerts.py` obliga a cotejar este hash, el manifiesto de primera emisión, 196 códigos únicos, 34 activos, 162 inactivos, probabilidades finitas interiores y fecha objetivo 2027. Elige los 15 casos mediante la regla escrita arriba, sin reentrenamiento, calibración, ajuste, selección de ventanas ni incorporación de hechos de 2026/2027.

**Si hay empate en la décima posición, quinta posición o dentro de la parte seleccionada, el generador se detiene**. No se introducen desempates discrecionales por nombre o ID. Se registra cada selección con código GW oficial, nombre de fuente, estado 2025, posición, probabilidad de transición y comparador global Markov original.

El nuevo documento pasa de *preparado* a *emitido* solo al existir un primer **commit público anterior a 2027** con las 15 probabilidades completas; el manifiesto ulterior fijará su SHA-256, commit y fecha obtenida de GitHub. El momento de ejecución local del generador no prueba ninguna fecha de emisión. GitHub no es notaría temporal independiente.

## Evaluación futura, sin mirar ahora los resultados

La **primera edición oficial completa** UCDP OrganizedViolenceCY que cubra 2027 será la única fuente primaria de etiquetas. Ningún país sin registro completo se interpreta como negativo; se conservarán por separado casos *unresolved* hasta disponer de una fuente válida para todos.

Para cada grupo de riesgo, se reportará:

- Número de cambios observados entre los **162/34** elegibles, aciertos dentro de las **10/5** alertas, precisión y recobrado si el denominador es no nulo. No se alterará el presupuesto tras conocer eventos.
- Diferencia de Brier condicional frente a `p_global_markov` original, y ROC AUC si existen ejemplos de ambas clases. El comparador y el estado inicial se congelan antes de los resultados. La referencia de no-transición determinista (probabilidad cero de cambio) se mostrará solo como análisis secundario de Brier.
- Distribución hipergeométrica de aciertos bajo asignación aleatoria de etiquetas dentro de los **conjuntos de riesgo** condicionados en su número de cambios futuro, con cola de obtener al menos los aciertos observados. Es un contraste de **intercambiabilidad** que puede violarse por dependencias geopolíticas.
- Se publicarán las dos probabilidades de cola originales y su corrección **Holm** para dos hipótesis en una familia, manteniendo la etiqueta de supuesto de intercambiabilidad. No se seleccionará ex post el extremo favorecido; ambas preguntas son independientes como objetivos declarados, pero no se supone independencia entre países.
- Calibración por grupo (riesgo previsto medio vs tasa de cambio), número de alertas correctas e incorrectas, y todas las pérdidas secundarias completas.

**Un éxito prospectivo no debe adjudicarse retroactivamente a las investigaciones 2023–2025**. Los tamaños de alerta 10/5 se eligieron después de observar resultados históricos; la nueva emisión de 2027 es prospectiva respecto al objetivo, pero su *diseño* no es independiente de la exploración histórica. Se informará esta distinción permanentemente.

## Límites de interpretación y privacidad

El modelo GEO usa la definición UCDP de violencia organizada **estatal** y no predice conflictos bélicos nuevos, homicidios totales, violencia contra civiles u otras formas de inestabilidad. Ni las probabilidades ni las alertas son diagnósticos políticos sobre países individuales. El uso operativo requeriría calibración futura, evidencia externa y evaluación explícita de falsos positivos.

Los datos de país y las probabilidades ya son públicos en la cohorte GEO institucional. **No se integran identidades personales, repositorios privados, cuentas personales, analíticas internas ni referencias a otras aplicaciones.**

Esta cohorte se publica como **resultado prospectivo no observado**; ninguna predicción de 2027 ni evento futuro se considera acertado antes de disponer de la fuente oficial.
