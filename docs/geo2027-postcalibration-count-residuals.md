# GEO-2027 — ¿Queda realmente sobredispersión después de corregir el sesgo marginal?

**12 de noviembre de 2026 · Análisis retrospectivo, no una nueva predicción.**

## Hipótesis falsable

Los estudios previos detectaron un exceso de cambios esperados respecto a los observados en las series UCDP históricas. Después, un calibrador de **solo dos interceptos** estimados con datos objetivo 2012–2019 mejoró la puntuación agregada de 2020–2025. Hasta ahora, la investigación de shocks compartidos había utilizado los residuos **antes** de corregir ese problema marginal.

La nueva pregunta es más estricta: **¿disminuyen los residuos de recuentos anualizados de entradas y resoluciones tras aplicar exactamente esos dos interceptos ya congelados?** Si ocurre, atribuir el exceso previo a dependencia sería especialmente endeble. Si no ocurre, tampoco demuestra por sí mismo dependencia: quedan errores marginales, cambios temporales, fuentes revisadas y shocks.

## Separación temporal y fuentes

Se evalúan por separado los grupos definidos **antes de observar el objetivo**: países inicialmente inactivos (entrada 0→1) y activos (resolución 1→0) respecto al umbral anual de al menos 25 muertes por violencia estatal.

- **Estimación histórica preexistente:** objetivos **2012–2019**, UCDP edición 26.1 revisada, únicamente para estimar los interceptos. **No** se cuentan estos años como verificación de ajuste.
- **Evaluación revisada:** objetivos **2020–2023**, reconstruidos con entrenamiento de cada año únicamente hasta `t−2`; etiquetas de la **edición 26.1** publicada en 2026, **no** verdaderas emisiones históricas con resultados notarizados.
- **Comprobación entre ediciones:** objetivos **2024 y 2025**, con UCDP **23.1 origen 2022 → 25.1 resultado 2024** y **24.1 origen 2023 → 26.1 resultado 2025**. Mismos 196 países por año y mismo conjunto de etiquetas del experimento anterior.

El protocolo utiliza los SHA-256 de las cuatro fuentes oficiales. También audita las primeras emisiones originales GEO-2027 y shadow, pero **no lee ningún resultado 2027**.

## Comparación exacta de tres modelos en los mismos países

En cada año objetivo y estado inicial se calcula `K = ∑y_i`, número de cambios binarios reales de umbral. Para cada uno de los tres modelos se calculan `E = ∑p_i` y `V_ind = ∑p_i(1−p_i)`. Los tres modelos son el Markov por país original, el Markov por país con el intercepto histórico fijo, y el Markov global original.

`Z=(K−E)/√V_ind` es el residual de recuento **condicional a independencia**; `Z²` y su media anual describen la discrepancia de recuentos bajo ese **escenario**. También se presentan el error agregado `∑(K−E)`, Brier, log-loss y la distribución Poisson-binomial exacta condicional a independencia, de la que se obtiene la masa acumulada para observar como máximo o como mínimo el recuento realizado.

**Advertencia metodológica obligatoria:** la distribución Poisson-binomial **no se presenta como prueba de significación ni p-valor inferencial válido**. Las probabilidades marginales ya pueden estar mal calibradas, la selección del calibrador es post hoc, los países no tienen por qué ser independientes y las observaciones consecutivas comparten países, horizontes bianuales y shocks.

Se muestra también, por año, el **producto de los dos residuos estandarizados** de entrada y resolución, antes y después de calibrar. Es una comparación descriptiva de signos, **no un estimador de correlación entre países**. En particular, con solo dos años objetivos entre ediciones no es posible distinguir una matriz de dependencia 196×196 de un cambio de calibración.

## Comprobaciones obligatorias

El script `scripts/diagnose_geo2027_postcalibration_count_residuals.py` coteja cada año y riesgo inicial con los recuentos anuales ya publicados en `data/geo2027-historical-count-dispersion-archival.json`; adicionalmente, sus Brier, interceptos y expectativas se contrastan con `data/geo2027-temporal-calibration-ablation.json`. La ausencia, duplicación o modificación de cualquier etiqueta origen/objetivo hace fallar la evaluación. Los 8 años de entrenamiento quedan **fuera** de la evaluación de dispersión calibrada.

Las pruebas sintéticas comprueban la separación 2012–2019 / 2020–2023 / 2024–2025, la igualdad de etiquetas entre modelos, el efecto de cambiar intercepto sobre esperanza y varianza y el rechazo de etiquetas ausentes, hashes alterados y mezclas de años.

## Limitaciones de identificación y regla de decisión

Esta investigación se eligió después de examinar los resultados históricos 2020–2025, por lo que ni una mejora de Brier, ni una menor razón de residuos, ni una acumulada Poisson-binomial extrema constituirán **evidencia confirmatoria**.

Se informa de valores **antes y después de la calibración** para cada año y estado inicial, sin seleccionar ni excluir años en función del resultado. Las comparaciones no modifican probabilidades GEO-2027, su segundo modelo shadow, las 15 alertas emitidas o NEWCONF-2027. Cualquier conclusión sobre shocks compartidos exigirá un programa adicional con hipótesis estructurales comprobables y muestras independientes de más años.

El informe completo se archivará como `data/geo2027-postcalibration-count-residuals-archival.json` y GitHub Actions deberá reconstruirlo byte a byte desde las fuentes UCDP oficiales.

## Datos reproducidos desde las fuentes UCDP originales

El informe `data/geo2027-postcalibration-count-residuals-archival.json` contiene cada año y cada estado inicial por separado, junto a tres modelos comparados **sobre idénticas etiquetas**. Se reconstruye desde las cuatro ediciones oficiales y se valida **byte a byte** en CI.

| Conjunto y transición | País-años | Cambios observados | Esperados originalmente | Esperados tras calibración | Media anual `Z²` original | Media anual `Z²` calibrada |
|---|---:|---:|---:|---:|---:|---:|
| 2020–2023, entradas | 651 | 19 | 29,18 | 22,31 | 1,326 | **0,581** |
| 2020–2023, resoluciones | 133 | 14 | 31,88 | 17,77 | 3,630 | **0,551** |
| 2024–2025, entradas | 321 | 8 | 13,50 | 10,31 | 1,225 | **0,277** |
| 2024–2025, resoluciones | 71 | 10 | 16,57 | 9,19 | 1,829 | **0,155** |

**El resultado cambia el diagnóstico:** en los dos grupos de riesgo y en ambos bloques, la discrepancia anual respecto a los recuentos esperados **cae notablemente** tras corregir las marginales. No es legítimo presentar la antigua sobredispersión como evidencia suficiente de correlación o contagio geopolítico.

Hay también **subdispersión descriptiva** frente al modelo Poisson-binomial bajo independencia en todos los bloques calibrados (media de `Z²` inferior a 1). Esto no prueba dependencia negativa, independencia ni que las probabilidades calibradas sean correctas: el denominador utiliza varianzas hipotéticas de eventos independientes, el método fue seleccionado tras explorar resultados de evaluación, las observaciones de años contiguos se solapan y la muestra separada solo incluye dos años.

### Diagnóstico anual que impide ocultar resultados adversos

El informe registra expresamente que en el periodo revisado **2022 las entradas observadas (7) superaron las esperadas tras calibración (~5,42)**, mientras que en 2020, 2021 y 2023 ocurrieron menos entradas que las esperadas. En las resoluciones revisadas se observaron **5 frente a 4,56 esperadas en 2022**, y menos de las esperadas en los otros tres años. El signo del residual, por tanto, **no es siempre negativo**.

En 2024, las resoluciones observadas fueron **6 frente a 4,90 esperadas** tras calibración; en 2025 fueron **4 frente a 4,29**. En ningún caso se excluyen años o riesgos por producir diferencias desfavorables. Se publican la Brier y el log-loss de los tres modelos y las masas Poisson-binomial, claramente marcadas como cálculos condicionales a independencia **no válidos como p-valores confirmatorios**.

### Implicación para PSICOHISTORIA

Con la evidencia disponible en 2026 **no está identificado un parámetro de dependencia entre países**. Lo que sí está documentado es que el error agregado de calibración explica parte importante de los residuos de recuentos históricos. Antes de aumentar la complejidad del modelo conjunto, se necesitarán más años realmente separados por edición y nuevas cohortes fechadas con criterios fijados antes de conocer sus resultados.

Permanecen inalterados el primer modelo GEO-2027, su shadow, las 15 alertas emitidas y NEWCONF-2027. **Ningún dato 2027 se ha observado ni incorporado.**
