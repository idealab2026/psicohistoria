# GEO-2027 — Ablación de calibración por estado inicial con separación temporal

**12 de noviembre de 2026. Investigación exploratoria, no emisión de probabilidades.**

## Hipótesis y limitación de selección

Los diagnósticos anteriores muestran sobreestimación de entradas y resoluciones al umbral de **25 muertes por violencia organizada estatal**. Para comprobar si un ajuste extremadamente sencillo puede mejorar las probabilidades históricas, se estudia un **desplazamiento constante del log-odds por estado inicial**. Esta idea se ha elegido *después* de inspeccionar los resultados agregados de 2024 y 2025. Por ello, la comparación sigue siendo **post hoc** aunque el cálculo use particiones temporales disjuntas. No debe presentarse como holdout confirmatorio ni como habilidad prospectiva certificada.

No se reentrena el modelo Markov original, ni se ajusta el orden de países, ni se modifica ningún vector emitido para 2027.

## Tres conjuntos con objetivos no solapados

1. **Estimación:** años objetivo **2012–2019**, edición UCDP OrganizedViolenceCY 26.1 con etiquetas históricas revisadas. Para cada año las probabilidades originales se reconstruyen solo con datos hasta su origen `t−2`. Se estiman *únicamente* dos interceptos `α_0, α_1`, uno para países inicialmente inactivos y otro para activos.
2. **Comprobación posterior revisada:** años objetivo **2020–2023**, misma edición 26.1, no utilizada para ajustar interceptos. La publicación real de las revisiones de etiquetas de esos años es de **2026**, no de sus fechas objetivo.
3. **Comprobación entre ediciones:** año objetivo **2024** con origen 2022 (23.1) y resultado 25.1, y objetivo **2025** con origen 2023 (24.1) y resultado 26.1. Ambos son los 392 país-años ya verificados y se comparan contra el informe histórico de recuentos archivado. Las ediciones posteriores solo aportan etiquetas, no predictores.

Los cortes son fijos; no se seleccionarán años, países ni coeficientes tras mirar los resultados de los bloques segundo o tercero.

## Método

Para cada estado de origen `s`, sea `q_i` la probabilidad Markov original de cambio en el horizonte de dos años: `q_i=p_i` si `s=0`, o `q_i=1−p_i` si `s=1`.

La propuesta mantiene el ranking estrictamente monótono:

\[
\tilde q_i=\operatorname{logit}^{-1}(\operatorname{logit}(q_i)+\alpha_s).
\]

Se determina `α_s` resolviendo, exclusivamente en 2012–2019,

\[
\sum_{i\in\mathrm{train}_s}\tilde q_i
=\sum_{i\in\mathrm{train}_s} y_i.
\]

Esto equivale a maximizar la verosimilitud Bernoulli respecto a un **intercepto único**. No es una estimación de dependencia, un entrenamiento geopolítico nuevo ni una garantía de calibración fuera de muestra.

Se reportan para los tres conjuntos **Brier**, **log-loss**, número de transiciones observado, número previsto originalmente y tras el ajuste, diferencia de pérdidas frente a Markov nacional original y Markov global original. Los resultados de 2024 y 2025 se muestran también por separado, para evitar ocultar un empeoramiento anual mediante un promedio combinado.

## Decisiones científicas

- Si mejora en 2020–2023 pero no en 2024–2025, se documentará la inestabilidad; no se probarán interceptos alternativos hasta conseguir una mejora aparente.
- Si mejora en ambos, sigue siendo **evidencia exploratoria retrospectiva**, porque el diseño se propuso tras inspeccionar agregados de esos periodos. Se requerirá un compromiso futuro verdaderamente nuevo para validar el efecto.
- Si no mejora, se reportará sin ajustes. En todos los casos se mantienen inalteradas las probabilidades, ranking, SHA y fechas de **GEO-2027** y **NEWCONF-2027**.

Los tests rechazan cambios de fuente, revisiones divergentes del informe anterior, cohortes incompletas, mezclas de estados y resultados fuera de los periodos definidos. Solo se publican agregados por periodo, año y estado, nunca etiquetas o scores individuales.

## Resultados reproducidos de las fuentes originales

El informe agregado `data/geo2027-temporal-calibration-ablation.json` se ha obtenido directamente de las fuentes oficiales UCDP con sus SHA-256 fijados. La CI exige su reproducción exacta **byte a byte**, junto con los tests que impiden entrenar usando etiquetas de validación.

Los multiplicadores estimados únicamente con los resultados de **2012–2019** son **0,746653** para el *odds* de entrada y **0,478668** para el de resolución. Son multiplicadores de *odds*, no de probabilidad lineal; el orden de países dentro de cada estado de origen se preserva estrictamente.

| Año objetivo y estado inicial | Cambios observados | Esperados originales | Esperados con intercepto | Diferencia Brier (ajustado − original) |
|---|---:|---:|---:|---:|
| 2020–2023, entradas | 19 | 29,18 | 22,31 | −0,00006733 |
| 2020–2023, resoluciones | 14 | 31,88 | 17,77 | −0,01824323 |
| 2024–2025, entradas | 8 | 13,50 | 10,31 | −0,00014371 |
| 2024–2025, resoluciones | 10 | 16,57 | 9,19 | −0,00604034 |

Una diferencia negativa favorece al candidato calibrado, pero estas observaciones están correlacionadas entre países y el diseño no es confirmatorio. Los *log-loss* del candidato también mejoran de forma agregada en ambos conjuntos.

**Heterogeneidad anual que no debe ocultarse:**

- Entradas 2024: **4** observadas frente a **5,14** esperadas tras ajustar; el Brier **empeora** +0,00002246.
- Entradas 2025: **4** observadas frente a **5,17** esperadas; el Brier mejora −0,00030681.
- Resoluciones 2024: **6** observadas frente a **4,90** esperadas; el Brier mejora −0,00024995.
- Resoluciones 2025: **4** observadas frente a **4,29** esperadas; el Brier mejora −0,01234165.

En 2012–2019 hubo **51 entradas** y **34 resoluciones** observadas; por construcción, el intercepto iguala la suma esperada al recuento de entrenamiento. Por ello, la mejora del ajuste dentro del conjunto de entrenamiento **no aporta evidencia de generalización**.

## Conclusión y restricción de investigación

Los resultados apoyan la hipótesis de que una porción significativa del error de recuentos históricos proviene de **calibración marginal** y no necesita ser atribuida a contagio o correlación entre países. No demuestran que el ajuste pueda trasladarse sin errores a 2027, menos aún que se mantenga la independencia entre eventos.

Se conservan sin cambios los pronósticos **GEO-2027** y **NEWCONF-2027**, la clasificación de las 15 alertas y sus hashes. El modelo calibrado queda solo como una **hipótesis secundaria candidata**, con la obligación de distinguir en el futuro sus métricas de las emitidas originalmente y no adjudicar retrospectivamente su mejora al pronóstico publicado.
