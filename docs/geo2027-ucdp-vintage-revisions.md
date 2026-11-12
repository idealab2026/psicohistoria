# GEO-2027 — Revisión de etiquetas UCDP e identificabilidad de shocks conjuntos

**12 de noviembre de 2026 · Investigación retrospectiva, edición controlada por SHA-256.**

## Problema científico

Una cifra anual de muertes de violencia estatal no es una observación inmutable: UCDP puede revisar información histórica al publicar una edición posterior. La pregunta de este estudio no es qué país pasará a guerra o paz en 2027, sino cuántas **etiquetas históricas de un mismo país y año** cruzan el umbral de **25 muertes** al cambiar de edición.

Esta variación editorial debe distinguirse rigurosamente de tres fenómenos distintos: una verdadera transición de un país **entre años**, el error de calibración de una probabilidad **emitida anteriormente** y una dependencia **entre países**. Un cambio de etiqueta por revisión de un mismo año no prueba ningún contagio geopolítico.

## Fuentes inmutables y método

Se usan exclusivamente las cuatro ediciones oficiales que ya forman el histórico de validación separada:

| Edición | Datos hasta | Formato |
|---|---:|---|
| UCDP 23.1 | 2022 | XLSX |
| UCDP 24.1 | 2023 | CSV ZIP |
| UCDP 25.1 | 2024 | CSV ZIP |
| UCDP 26.1 | 2025 | CSV ZIP |

Las URL institucionales y los SHA-256 de cada edición están en `scripts/backtest_archived_country_vintages.py`. Ningún cambio de origen de datos es admisible sin declarar un experimento distinto. Se utiliza el campo `sb_total_deaths_best` exclusivamente para el indicador binario de violencia **estatal**.

Se cotejan todas las observaciones de **igual país y año**, con separación entre etiqueta 0→1, etiqueta 1→0, estabilidad en ambos estados y observaciones ausentes. Estas últimas jamás se rellenan como cero. Se contrastan **tres pares sucesivos** (23.1→24.1, 24.1→25.1 y 25.1→26.1) y **dos comparaciones saltando una edición** (23.1→25.1 y 24.1→26.1), incluyendo desglose anual para 2018–2024 cuando el año ya estaba cubierto por la primera edición.

Los recuentos agregados incluyen su denominador exacto de pares observados en ambas fuentes. El número neto de países activos puede mantenerse constante aunque se hayan cambiado **dos o más etiquetas individuales**, circunstancia que afecta la puntuación por país de un pronóstico sin alterar necesariamente el número total de transiciones.

## Sensibilidad específica de la evaluación archivada de 2024

La comparación histórica GEO ya existente entrenó el modelo sobre **UCDP 23.1 hasta 2022** y evaluó **196 países** en 2024 según la primera edición completa del objetivo, **UCDP 25.1**. Ese mismo 2024 puede comprobarse ahora contra la edición posterior **26.1**.

La nueva comprobación reutiliza **exactamente las 196 probabilidades originales de aquel experimento**. Solo reemplaza las etiquetas históricas 2024 de la fuente posterior. Calcula los Brier y log-loss del Markov nacional y global, separados por el estado conocido en origen (2022), y registra cuántos cambios de clasificación o de umbral aparecen.

No se permite recalibrar a partir de 26.1, escoger otro conjunto de países ni usar una etiqueta 2025 para resolver el objetivo 2024. La revisión de 2024 se compara como **sensibilidad secundaria**; el resultado de la primera edición 25.1 **no se sustituye**.

La evaluación histórica de 2025, con etiqueta de 26.1, **no tiene todavía una edición posterior verificada** dentro de este conjunto de fuentes. Se declara `null` su análisis de revisiones y no se inventa su estabilidad.

## Por qué no es posible estimar una dependencia 196×196 con dos años

Con el histórico de **dos objetivos separados por edición** (2024 y 2025), no existe información temporal suficiente para identificar una matriz libre de correlaciones de 196 países. Aunque todos fueran observados de forma homogénea cada año, la matriz de covarianza muestral centrada tendría **rango máximo 1** (con dos vectores temporales). Los 196 países implican **19.110 covarianzas cruzadas** potenciales. Un estimador de covarianza empírica no singular sin restricciones necesitaría al menos **197 observaciones anuales** completas, que además deberían satisfacer hipótesis probabilísticas adicionales para ofrecer inferencia válida.

La versión histórica retrospectiva de **12 años** presenta a lo sumo rango **11** y, además, utiliza etiquetas revisadas de una sola edición 2026, no un conjunto de predicciones genuinamente emitidas entonces. El argumento de rango es un **límite algebraico**, no una afirmación de que la independencia sea verdadera ni de que 197 años garantizarían una estimación fiable.

Aún son posibles análisis espaciales/sectoriales con una estructura mucho más restringida y definida previamente, pero cualquier coeficiente de dependencia estimado necesitaría una validación en ediciones fechadas independientemente y muestras adicionales. Ajustar ya una matriz 196×196 para predecir 2027 sería sobreajustar por construcción.

## Gobernanza y reproducibilidad

El informe resultante `data/geo2027-ucdp-vintage-revisions-archival.json` contendrá únicamente recuentos agregados por edición y año, la sensibilidad histórica de Brier/log-loss y la advertencia de no identificabilidad. La auditoría comprobará las cuatro fuentes originales, sus hashes, la cohorte histórica de 392 país-años, la cobertura 196 del objetivo 2024 y la coincidencia exacta de las etiquetas de la edición primera. Pruebas sintéticas aseguran que una revisión no se convierte falsamente en transición real y que una etiqueta faltante bloquea su uso.

Los 196 pronósticos GEO-2027, el segundo modelo shadow, las 15 alertas originales, NEWCONF-2027, todos sus documentos de primera emisión y sus fechas permanecen **completamente inalterados**. El estudio no aporta ninguna observación real de 2027 ni prueba capacidad predictiva futura.

## Resultados verificables: revisiones reales de cuatro ediciones

El informe completo, reproducido desde las fuentes UCDP con los cuatro SHA-256, está archivado en `data/geo2027-ucdp-vintage-revisions-archival.json`. Cada auditoría posterior debe recomputarlo y confirmar **igualdad exacta de los bytes**.

| Edición inicial → posterior | Países-año idénticos | Cambios 0→1 | Cambios 1→0 | Total de etiquetas revisadas |
|---|---:|---:|---:|---:|
| 23.1 → 24.1 | 6.544 | 1 | 1 | **2** |
| 24.1 → 25.1 | 6.740 | 4 | 0 | **4** |
| 25.1 → 26.1 | 6.936 | 2 | 1 | **3** |
| 23.1 → 25.1 | 6.544 | 5 | 1 | **6** |
| 24.1 → 26.1 | 6.740 | 6 | 1 | **7** |

Estas comparaciones **no son muestras independientes**: los pares que saltan una edición solapan los pares consecutivos. No se suman los cambios para obtener una tasa total única. La variable describe el cruce del umbral binario entre dos ediciones de un **mismo país y mismo año**, no el número de conflictos que comenzaron o terminaron.

### Caso particularmente informativo: las 196 etiquetas del objetivo 2024

En los **196 países exactos** del diagnóstico con origen 2022 (edición 23.1), la primera edición de etiquetas objetivo 2024 (25.1) y su revisión posterior (26.1) coinciden completamente:

| Bloque fijado por estado de origen en 2022 | Países | Transiciones 2024 según 25.1 | Transiciones 2024 según 26.1 | Variación de Brier |
|---|---:|---:|---:|---:|
| Inicialmente inactivos | 159 | 4 | 4 | **0** |
| Inicialmente activos | 37 | 6 | 6 | **0** |
| **Total** | **196** | **10** | **10** | **0** |

Ambas fuentes clasifican como activos en 2024 a los mismos **35 países** y como inactivos a los otros **161**. También son exactamente iguales las diferencias de log-loss de aquel diagnóstico al cambiar de edición. No hay ninguna revisión de umbral en ese corte 2024.

**Inferencia permitida:** el sesgo de calibración detectado en ese diagnóstico de 2024 **no se explica por revisiones de etiquetas 2024 entre 25.1 y 26.1**. **Inferencia no permitida:** concluir que el modelo está mal calibrado en 2027 o que 2025 será estable frente a ediciones futuras. El corte de 2025 solo se ha observado en 26.1.

### Dependencia entre países: no identificada

Las dos cohortes anuales 2024–2025 constituyen únicamente **dos bloques temporales** para el análisis de shocks compartidos. La matriz de covarianza empírica centrada en un espacio de **196 países** tendría rango máximo **1** con dos observaciones, independientemente del algoritmo empleado. Una matriz sin restricciones contiene **19.110 pares de covarianza**; incluso los 12 años revisados de otras pruebas tendrían rango máximo 11 y además no son cohortes archivadas con las fechas correspondientes.

No se ha inferido ninguna correlación, ni se ha aplicado una matriz regularizada elegida retrospectivamente, ni se ha ajustado el número de alertas. La investigación continúa separando **revisiones de fuentes, calibración marginal y dependencia conjunta** en lugar de amalgamarlas en una supuesta mejora predictiva.
