# PSICOHISTORIA — Contrato de resolución futura de alertas GEO-2027

**11 de noviembre de 2026 · Contrato preparado, resultados de 2027 inexistentes.**

Este protocolo hace ejecutable el compromiso prospectivo público de la [cohorte secundaria de alertas GEO-2027](../data/forecast-2027-transition-alerts-manifest.json). No genera nuevas predicciones, no introduce datos posteriores a 2025 y no declara éxito predictivo.

## Inmutabilidad y trazabilidad

El script `scripts/evaluate_geo2027_transition_alerts_official.py` autentica conjuntamente:

- Las **196 probabilidades originales GEO-2027**, SHA-256 `5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5`.
- Las **15 alertas derivadas**, SHA-256 `309b4f270e1d0d6382b7a90ae64c28d7621f96fbf3177a45aaebbffb0f958acb`.
- Primera fecha pública de las alertas, commit `5938db3c93661ce04ed35902b2bdaa68abfb8daa` (11/11/2026, 19:28:31 UTC), documento canónico y auditoría registrada.
- El mismo código generador; cualquier variación exige un nuevo informe sin alterar las alertas ya emitidas.

Solo se permite aportar un **ZIP de UCDP OrganizedViolenceCY** oficialmente identificado, con URL literal del dominio `ucdp.uu.se`, archivo de edición a partir de **28.1**, SHA-256 íntegro calculado sobre sus bytes y fecha de publicación declarada posterior al 31/12/2027. Estos atributos se comprueban técnicamente, pero **no certifican por sí solos** que el operador haya seleccionado la *primera edición oficial completa*; este extremo requiere verificación independiente.

El parser exige cabeceras país, año y `sb_total_deaths_best`; detecta cabeceras duplicadas, registros duplicados, códigos fuera de rango, años inválidos, muertes negativas, formatos no enteros y fuentes sin 2027. Un campo de muertes vacío se registra como **etiqueta no resuelta**, nunca como ausencia de conflicto. La extracción solo utiliza el **año objetivo 2027**; los demás años no son evidencia de resultado para este protocolo.

## Dos endpoints cerrados

| Riesgo conocido en 2025 | Universo inmutable | Alertas emitidas | Éxito a evaluar |
|---|---:|---:|---|
| Entrada (0→1) | 162 | 10 | Estado 2027 activo (≥25 muertes) |
| Resolución de umbral (1→0) | 34 | 5 | Estado 2027 inactivo (menos de 25 muertes) |

**Condición de completitud:** solo si se resuelven los **196 países originales** se calculan los dos conjuntos de métricas. Si falta incluso un país, se devuelve cobertura, número e IDs no resueltos, y ambos endpoints permanecen `null` para no confundir una selección parcial con éxito.

Con cobertura completa se publican, separadamente por endpoint:

1. Eventos de transición en todo su universo, eventos dentro de las alertas, alertas sin cambio, precisión y recobrado (no definido si no hay transiciones).
2. Probabilidad media prevista de transición y Brier, frente al **Markov global emitido** y la referencia determinista sin cambios.
3. AUC ROC con medio crédito para empates y área precisión-recall calculada por grupos de empates, solo cuando exista soporte estadístico suficiente.
4. Valor esperado de aciertos bajo el modelo congelado, y valor esperado bajo asignación aleatoria de etiquetas, condicionado al total de eventos oficiales.
5. Cola hipergeométrica exacta `P(X≥aciertos)` bajo **intercambiabilidad de países dentro del conjunto de riesgo 2025**, y **Holm** para los dos endpoints preregistrados. Son contrastes condicionados cuya interpretación no requiere independencia entre el número de entradas y resoluciones, pero sí la hipótesis fuerte de intercambiabilidad para cada cola aleatoria.

La corrección de Holm es un ajuste formal de dos contrastes; no subsana sesgos históricos en el diseño, dependencia regional, selección de hipótesis ni posibles revisiones futuras.

## Estados y límites

La salida siempre queda como `CANDIDATE_PARTIAL_COVERAGE_NO_SCORES` o `CANDIDATE_FULL_COVERAGE_STILL_UNCERTIFIED`. Las siguientes banderas permanecen **falsas**, aunque las métricas parezcan excelentes:

- `source_first_complete_release_independently_attested`
- `prospective_skill_independently_certified`

El valor científicamente útil exige una auditoría separada de la **primera publicación UCDP completa para 2027**, del método de correspondencia de países, de la fuente descargada, de la integridad de todos los valores y del registro temporal de esta emisión de 2026. No se confundirán el nacimiento de conflictos `newconf`, las transiciones del umbral de víctimas o las resoluciones políticas.

## Pruebas antes de que llegue 2027

GitHub Actions ejecuta pruebas con **etiquetas 2027 completamente ficticias**: casos positivos y negativos, ausencia de una etiqueta dentro o fuera de la selección, nula incidencia de cambios, errores de fecha/URL/huella, duplicados, valores inválidos, cálculo de Holm y límites de cohortes. Las pruebas autentican el manifiesto emitido y prohíben calcular puntuaciones con denominadores incompletos.

No existe ninguna ejecución automática de resultados futuros ni se ha simulado una publicación oficial real. Ningún informe de resultados de 2027 se agrega a `data/` mientras esa fuente oficial no esté disponible y auditada.
