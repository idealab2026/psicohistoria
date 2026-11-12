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
