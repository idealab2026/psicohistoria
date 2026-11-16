# GEO2027 LOG1P · Estabilidad cronológica de Brier por año y por edición UCDP

**Protocolo de diagnóstico retrospectivo · 16/11/2026.** No modifica ninguno de los pronósticos o alertas originales de 2027. No emite otras predicciones prospectivas.

## Pregunta científica

Los experimentos precedentes de atenuación de la pendiente LOG1P mostraron **una contradicción temporal**: 2024 favoreció la intensidad completa (α=1), mientras 2025 favoreció su supresión entre países inactivos (α=0). Para saber si esa variación responde a una excepción de dos años o a inestabilidad más general, calculamos **series anuales completas con ventana temporal rodante y sin fuga de etiquetas posteriores**.

Las cinco alternativas LOG1P son **las mismas ya analizadas**, α∈{0;0,25;0,5;0,75;1}, sin reentrenar un modelo diferente para cada α; se conserva el Markov H2 original como offset logit, el intercepto logístico y la pendiente de los países originalmente activos. Se atenúa exclusivamente el coeficiente de intensidad para el grupo de origen inactivo.

## Corte temporal estricto en cada año objetivo

Para un año objetivo retrospectivo \(t\), el **origen de pronóstico es \(o=t-2\)**. Se calcula la probabilidad Markov original usando datos **hasta \(o\)**. La regresión LOG1P utiliza un conjunto de entrenamiento de observaciones históricas con años objetivo \(u=2012,\dots,o\); cada una tiene su propio origen retrospectivo \(u-2\). Por tanto:

- La **etiqueta más reciente usada para ajustar \(\beta_t\)** es la del año \(o=t-2\), **no** la del año \(t-1\). Esto es más conservador que entrenar hasta \(t-1\) cuando el forecast de horizonte dos ya debía estar fijado.
- El **predictor histórico más reciente** del ajuste de \(\beta_t\) utiliza datos hasta \(o-2=t-4\), porque las observaciones de entrenamiento también son forecasts H2 anidados.
- La evaluación en \(t\) parte de los **196 identificadores de referencia** emitidos en 2027, pero incluye únicamente los países con estado de origen y etiqueta de año objetivo **observados** en esa edición. Se registra cuántos faltan en cada año histórico y **nunca se les imputa cero**; el universo efectivo puede ser menor que 196. El score se desglosa por año, no solo sobre sumas de países-año.
- La penalización ridge se mantiene en **λ=5**, fijada en la investigación anterior. **No es una elección legítimamente ex ante para años como 2017–2020:** se adoptó en 2026 tras inspeccionar resultados históricos. Por ello esto mide exclusivamente estabilidad interna bajo un método fijado *ahora*, no demuestra cómo habría funcionado un sistema publicado en cada año anterior.

Se utilizan **cuatro ediciones originales UCDP OrganizedViolenceCY**, verificadas contra SHA-256: 23.1 (hasta 2022), 24.1 (hasta 2023), 25.1 (hasta 2024), 26.1 (hasta 2025). Se recalculan las series 2017–último año de cada edición: **6+7+8+9 = 30 observaciones año-edición, pero solamente 9 años objetivo distintos (2017–2025)**. Los años 2017–2022 están presentes en las cuatro ediciones y constituyen **el mismo histórico revisado**, no cuatro réplicas independientes.

## La diferencia entre causalidad cronológica y disponibilidad histórica real

Una regresión cuyo ajuste solo utiliza \(u\leq t-2\) evita *fuga de etiquetas posteriores en el algoritmo*. No garantiza que las **versiones de los registros disponibles en 2017 o 2019** fueran exactamente iguales a las de UCDP 23.1 (publicada en 2023) o 26.1 (publicada más tarde). De hecho, estudios anteriores del laboratorio documentaron revisiones explícitas del número de muertes. Este análisis es, por tanto, **una reconstrucción ex post por edición**, no una validación walk-forward con fuentes notarizadas como disponibles en cada fecha.

Además, los años 2018–2020 sirvieron anteriormente para escoger regularización, y 2024–2025 ya se examinaron para la familia LOG1P; por tanto no constituyen conjuntos de confirmación vírgenes para ninguna variante. No deben elegirse nuevas pendientes basándose en los recuentos de años favorables que surjan ahora.

## Resultados reproducidos desde las cuatro ediciones oficiales

Las cuatro reconstrucciones contienen **30 bloques año–edición** en conjunto (6 en 23.1, 7 en 24.1, 8 en 25.1 y 9 en 26.1). Solo existen **9 años objetivo diferentes (2017–2025)**. En el intervalo de evaluación 2017–2025 los 196 países de referencia tienen etiquetas observadas en las fuentes recuperadas, aunque el código continúa **excluyendo explícitamente** cualquier país-año faltante en periodos más antiguos en lugar de imputarlo como negativo.

La comparación principal es la diferencia \(\Delta Brier=Brier_{\alpha=1}-Brier_{\alpha=0}\), **negativa si conserva mejor puntuación la señal continua completa**. Ambos modelos se reentrenan para cada año objetivo con etiquetas disponibles *solamente hasta dos años antes* y con la misma penalización ridge 5, **no optimizada individualmente por año**.

| Año objetivo | Ediciones donde aparece | \(\Delta Brier\) UCDP 26.1 | Interpretación retrospectiva |
|---|---:|---:|---|
| **2017** | 4 | +0,000111 | Favorece **α=0**, desactivar intensidad inactiva |
| **2018** | 4 | −0,000962 | Favorece α=1, señal completa |
| **2019** | 4 | −0,000936 | Favorece α=1 |
| **2020** | 4 | **−0,002072** | Mayor ventaja observada para α=1 |
| **2021** | 4 | −0,000324 | Favorece α=1, ventaja limitada |
| **2022** | 4 | −0,000336 | Favorece α=1, ventaja limitada |
| **2023** | 3 | −0,000676 | Favorece α=1 |
| **2024** | 2 | −0,000788 | Favorece α=1 |
| **2025** | 1 | **+0,000620** | Favorece **α=0** |

**Balance: α=1 alcanza menor Brier en 7 de los 9 años distintos; α=0 lo alcanza en 2017 y 2025.** En la edición UCDP 26.1, el promedio anual (cada año pesa una vez; la cohorte evaluable tiene 196 observaciones por año) es **0,037980** para α=1 y **0,038576** para α=0. La diferencia de −0,000596 es descriptiva, no un estimador prospectivo validado.

### Estabilidad temporal frente a estabilidad de edición

- **Variación entre años:** en UCDP 26.1 la dirección del efecto cambia dos veces: de 2017 a 2018 y de 2024 a 2025. En los archivos que terminan en 2022–2024, solo se observa el primer cambio. Esto es coherente con una señal que puede ser históricamente útil **sin ser uniformemente estable año a año**.
- **Variación de edición para el mismo año:** **0 de los 8 años** con dos o más ediciones disponibles cambian de signo en \(\Delta Brier\). La dirección es estable frente a estas revisiones oficiales concretas, pero la *magnitud* puede variar bastante.
- **Ejemplo concreto de sensibilidad editorial:** para objetivo **2022**, la ventaja de α=1 disminuye de **−0,001810** usando edición **23.1** a **−0,000336** usando edición **26.1**; aproximadamente **5,4 veces menor en valor absoluto**, sin cambiar el signo.
- **Relación con los estudios de emisiones anteriores:** la reconstrucción anual por edición utiliza **las etiquetas objetivo incluidas en esa misma edición retrospectiva**; no reproduce las comparaciones estrictas entre ediciones de origen y objetivo de los estudios anteriores. Son diseños distintos y no deben mezclar sus Brier en una sola tabla como si fueran una replicación exacta.

### Regla de interpretación

No inferimos que 7/9 equivalga a «probabilidad 77,8 % de superioridad»: los años tienen dependencias, las fuentes han sido revisadas y la familia de parámetros λ=5 / α se decidió tras observar parte de este histórico. Tampoco se realiza un test binomial o IID de significación porque violaría esas hipótesis.

**Conclusión provisional:** la señal continua no es simplemente una mejora de 2024: su ventaja de Brier reaparece desde 2018 hasta 2024 en el mismo protocolo retrospectivo, con diferencias de tamaño variables. El fallo de 2025 no se oculta. Esta combinación refuerza mantener **la sombra prospectiva LOG1P original congelada** para evaluar 2027 sin retocarla y mantener por separado el diagnóstico de fragilidad editorial ya comprobado.

## Métricas y diagnóstico

Para cada versión y cada año objetivo \(t\) se publica **Brier y log-loss por α**, Brier del Markov original, **número exacto de países observados de los 196 de referencia**, cobertura histórica faltante, número de países positivos (≥25 muertes estatales), estados activos al origen, tamaño exacto del conjunto de entrenamiento, coeficientes y trazas de los cortes temporales. Se reporta la diferencia \(\Delta_t = Brier_{\alpha=1,t} - Brier_{\alpha=0,t}\): negativa si favorece la intensidad completa; positiva si favorece la supresión entre inactivos.

Se cuantifican los **cambios de signo de \(\Delta_t\)** entre años contiguos de una misma edición y se compara el signo para el mismo año entre ediciones que revisaron el histórico. Esas discrepancias ayudan a separar **inestabilidad temporal del método** de **inestabilidad editorial de UCDP**. La comparación de medias por versión es puramente descriptiva; no se calcula un valor-p asumiendo independencia de países-año o versiones.

**Protección de emisiones:** se verifican los archivos inmutables de GEO2027 original (SHA-256 \`5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5\`), de la sombra LOG1P (SHA-256 \`52686923315854557a796f8f192d376dab77a4e03b14c1aeb6b4091e48104f90\`) y de las 15 alertas (SHA-256 \`309b4f270e1d0d6382b7a90ae64c28d7621f96fbf3177a45aaebbffb0f958acb\`). **Cero resultados de 2027 resueltos; ninguna emisión nueva.**

Los controles de CI reproducen el documento y sus datos a partir de las cuatro fuentes SHA-verificadas con comparación byte a byte. Las pruebas sintéticas cambian intencionadamente etiquetas \(t-1\) y años posteriores para verificar que los coeficientes ya ajustados en \(t-2\) permanecen idénticos.

Código: \`scripts/experiment_geo2027_log1p_rolling_year_vintage.py\`; pruebas: \`scripts/test_experiment_geo2027_log1p_rolling_year_vintage.py\`; informe: \`data/geo2027-log1p-rolling-year-vintage-stability.json\`.

