# GEO H2 · Cambio observado del Brier atribuible solo a etiquetas revisadas

**Estudio retrospectivo reproducible, 18/11/2026.** Se compara la definición de violencia estatal `sb_total_deaths_best ≥ 25` de UCDP OrganizedViolenceCY **25.1 frente a 26.1** en los 196 países GWNO congelados, objetivos históricos **2014–2024**.

Para cada origen (objetivo menos dos años), se reconstruye una única pareja de vectores de probabilidades desde la misma edición de entrenamiento, mediante el modelo Markov binario, cuatro estados, global Markov y prevalencia quinquenal ya publicados. Las dos evaluaciones utilizan exactamente esas mismas probabilidades y los mismos 196 países; **solo cambia la etiqueta de la edición objetivo**. La igualdad de las probabilidades se comprueba por país.

Para cada modelo, el cambio medido de Brier es la suma de `(y_nueva−y_antigua)(1−2p)/N`. Se puede medir separadamente el efecto sobre las diferencias Brier entre pares de modelos, sin comparar modelos reentrenados ni mezclar cambio de etiqueta con cambio de pronóstico.

**No es un test prospectivo:** se construyen retrospectivamente probabilidades para años antiguos con ediciones que no existían entonces; el archivo oficial conserva revisiones posteriores incluso en las features anteriores al origen. El modelo original GEO2027, las sombras, alertas y GEO2028 permanecen inalterados.

Los datos reales deben proceder de la descarga y verificación SHA de los archivos UCDP oficiales, nunca de completar países ausentes con cero. El programa comprueba el universo de países, el estado inicial, los parámetros y las etiquetas contra el informe histórico publicado con anterioridad.

**Resultado SHA-reproducido:** el primer replay de CI identificó **1 etiqueta binaria revisada de 2.156 país-años** (11 objetivos 2014–2024 × 196 GWNO). El GWNO **100** en **2017** pasó de **23 fallecidos en 25.1 (estado 0)** a **65 fallecidos en 26.1 (estado 1)**. El origen modelado es 2015 y se utiliza la edición de entrenamiento 23.1 **en ambas evaluaciones**: los cuatro pronósticos están fijos.

| Modelo fijo | Cambio de Brier al sustituir etiquetas 25.1→26.1 |
|---|---:|
| Markov binario | −0,0003275294 |
| Markov cuatro estados | −0,0003664688 |
| Markov global | −0,0001671033 |
| Prevalencia global 5 años | +0,0003306266 |

La diferencia de Brier **cuatro estados menos binario** se desplaza **−0,0000389394**. Es un beneficio relativo de la revisión de la etiqueta a favor de cuatro estados, no prueba de superioridad predictiva global: aquí solo se examina el *desplazamiento* del score, no su nivel absoluto. No se puede sumar como dato independiente a otros backtests solapados.

Las probabilidades originales fijas del país revisado fueron **0,853076712368** (binario), **0,895053377691** (cuatro estados), **0,680137325986** (global) y **0,143584521385** (prevalencia). El cambio puntual de contribución del país es −0,7061534 para el binario y −0,7901068 para cuatro estados, dividido entre 2.156 casos para obtener el efecto global.

**Cota versus medición real:** la cota de desplazamiento absoluto de un modelo fijo era 1/2156 = **0,0004638219**; la variación medida no la alcanza. Los once años son años objetivo diferentes de un mismo panel, no 2.156 países estadísticamente independientes.

**Verificación:** el reporte oficial congelado [JSON](../data/geo-h2-fixed-vector-2526-outcome-revision.json) se reproduce y coteja por igualdad exacta de los valores JSON por [script](../scripts/experiment_geo_h2_fixed_vector_outcome_revision.py) en CI; las [pruebas sintéticas](../scripts/test_experiment_geo_h2_fixed_vector_outcome_revision.py) verifican la identidad y rechazan pronósticos no idénticos. Las fechas de las fuentes de origen siguen impidiendo una validación prospectiva histórica.
