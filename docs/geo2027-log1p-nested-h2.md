# GEO2027 · Intensidad continua log(1+muertes) con selección temporal anidada

**Protocolo y registro científico · 16 de noviembre de 2026.** Es un experimento de investigación retrospectivo, no una reemisión de GEO2027/28, ni una demostración de capacidad predictiva prospectiva. Los resultados oficiales de 2024/25 **ya fueron observados en anteriores estudios del laboratorio**: ninguna comparación sobre esos años puede considerarse una muestra virgen de confirmación, aunque los coeficientes solo se ajusten con años anteriores.

## Pregunta

¿La intensidad continua de las muertes por violencia estatal (UCDP OrganizedViolenceCY, columna oficial de muertes best) agrega señal sobre el modelo binario **ya emitido** que predice exceder el umbral anual de **≥25 muertes** en horizonte H2?

Para no confundir recalibrar la prevalencia de eventos con aprovechar el conteo continuo de muertes, se incluyen **tres modelos y un control adicional histórico**:

1. **Original GEO H2:** Markov binario 2 estados, Laplace global 1, shrinkage local 20, dos pasos; ecuaciones y probabilidades intactas. Su Brier y log-loss se deben reproducir exactamente respecto al informe oficial de comparación entre ediciones.
2. **Control de recalibración solo-intercepto:** regresión logística unidimensional con el **logit del GEO original como offset fijo**. La corrección utiliza únicamente una constante ajustada sobre las etiquetas temporales internas.
3. **Alternativa continua log(1+muertes):** mismo offset, intercepto y dos coeficientes sobre funciones continuas de las muertes en el año del origen. Un coeficiente para datos de 0–24 (inactivos), otro para ≥25 (activos). Se estiman mediante log-verosimilitud con regularización L2 y ninguna librería estadística externa; el criterio primario de validación es Brier.
4. **Cuatro estados:** informe previo (0, 1–24, 25–99, ≥100), registrado como antecedente y referencia secundaria descriptiva, **no usado para selección**.

El predictor logit queda formalizado como:

\[
\operatorname{logit}p_{\mathrm{continuo}}=
\operatorname{logit}p_{\mathrm{GEO}}
+\beta_0+\beta_I x_I+\beta_A x_A
\]

Con **muertes originales** \(d_t\), medidas en el año de origen:

\[
x_I=1(d_t<25)\frac{\log(1+d_t)}{\log(26)},\qquad
x_A=1(d_t\geq25)\frac{\log(1+d_t)-\log(26)}{\log(101)}.
\]

Esto utiliza la intensidad como variable continua *dentro de cada estado binario* y mantiene el riesgo original como offset, no intenta predecir el propio logaritmo de las muertes. La separación en dos pendientes tiene una discontinuidad convencional en el umbral, ya presente en el estado GEO; no debe confundirse con una ley empírica demostrada.

## Cronología de entrenamiento, ajuste y evaluación

Se usan dos comparaciones con archivos **UCDP oficiales distintos** para el origen y el objetivo: 23.1 hasta 2022 → 25.1 en 2024; 24.1 hasta 2023 → 26.1 en 2025. Los cuatro documentos originales son reconstruidos a partir de bytes verificados por SHA-256.

Para cada edición de origen se crean retrospectivamente observaciones anuales con años objetivo **2012 hasta el propio año de origen**; para cada objetivo interior \(t\), las probabilidades GEO y las variables explicativas se calculan **solo** con los datos hasta \(t-2\), y el resultado \(t\) procede de la **misma** edición de origen. No se construyen predicciones interiores a partir de todo el histórico, lo que produciría fuga temporal.

| Función | Años objetivo | Regla |
|---|---|---|
| **Ajuste interno para selección** | 2012–2017 | Entrenar cada candidato lambda con estos objetivos; para cada uno, predictores observados hasta dos años antes |
| **Validación interna cronológica** | 2018–2020 | Elegir lambda por Brier mínimo, sin incorporar esos años a los coeficientes provisionales |
| **Reentrenamiento definitivo** | 2012–2022, o 2012–2023 | Ajustar coeficientes completos, con el lambda previamente elegido, **solo** sobre la edición del origen |
| **Resultado externo exploratorio** | **2024** y **2025** | Fijar coeficientes y predecir H2 antes de consultar la etiqueta de la edición posterior |

Se prueban exactamente las penalizaciones L2 **λ = 5, 20 y 80**, sin elegir otras después de observar 2024/25. Se penalizan intercepto y pendientes por igual. El control solo-intercepto utiliza **el mismo λ seleccionado previamente**. Esta comparabilidad evita atribuir al conteo continuo una ganancia debida exclusivamente a la recalibración de prevalencia.

## Métricas y criterios de decisión

**Resultado principal:** Brier pareado continuo menos GEO binario en los 392 casos de dos años, con log-loss como métrica secundaria. **Prueba imprescindible de valor incremental:** Brier continuo menos Brier del control solo-intercepto, además del resultado contra GEO. Se desagregan año, origen activo/inactivo e intensidad previa. También se reportan coeficientes, lambda seleccionado de forma anidada, positivos en desarrollo y validación, y países con mejores/peores contribuciones.

**Nunca inferir** que 2024/25 son un holdout genuinamente independiente: los análisis anteriores de cuatro estados y de revisiones de datos ya mostraron sus resultados. Esta limitación afecta a la **interpretación a nivel de programa de investigación**, aunque el algoritmo internamente no haya visto esos resultados durante el ajuste. La validación interna 2018–2020 usa **una sola versión retrospectiva** para sus resultados; no hay garantía independiente de fecha de publicación original de esos datos. Dos resultados anuales, países repetidos y choques globales comunes no permiten intervalos IID ni conclusiones causales.

Los expedientes futuros y sus métricas **siguen sin resultados oficiales certificados**; el experimento no reemplaza ninguna emisión 2027/28. Incluso si una alternativa supera las métricas históricas, no debe pasar automáticamente a producción: requeriría un protocolo y emisión nuevos, con evaluación posterior genuinamente fuera de muestra.

## Resultados obtenidos de los cuatro archivos UCDP verificados

La fuente oficial reproduce **exactamente** la referencia GEO binaria de los dos estudios anteriores (misma cohorte de 196 países, 35 positivos en 2024 y 34 en 2025). El experimento utiliza dos ajustes logísticos, ambos **entrenados sobre la edición de origen antes de consultar resultados en la edición posterior**. Es una comparación **retrospectiva exploratoria con holdouts previamente vistos**.

| Brier (menor es mejor) | GEO binario original | Control intercepto | GEO + log(1+muertes) |
|---|---:|---:|---:|
| 2024 · 196 países | 0,04143146 | 0,04116664 | **0,03795997** |
| 2025 · 196 países | 0,03873665 | 0,03829956 | **0,03682690** |
| **Total · 392 observaciones** | 0,04008406 | 0,03973310 | **0,03739343** |

| Log-loss (menor es mejor) | GEO original | Control intercepto | GEO + log(1+muertes) |
|---|---:|---:|---:|
| **Total** | 0,15439774 | 0,15445999 | **0,13868762** |

La mejora del Brier de la alternativa continua sobre el binario es **−0,00269062** (un **6,7 % relativo**), y sobre el intercepto de control es **−0,00233967**. En log-loss: **−0,01571011** respecto al original y **−0,01577236** respecto al control. Esto apoya, dentro de los datos examinados, una señal de intensidad continua adicional a una simple recalibración.

### ¿Qué aprendió la selección temporal interna?

Para cada una de las dos ediciones originales, el entrenamiento interior (2012–2017) produjo aproximadamente **1.174 observaciones**, y la evaluación temporal interior (2018–2020), **588 observaciones**. Las tres penalizaciones predefinidas ofrecen los siguientes Brier de validación de intensidad:

| λ | Orig. 2022 · validación 2018–2020 | Orig. 2023 · validación 2018–2020 |
|---|---:|---:|
| **5** | **0,03944017** | **0,03929446** |
| 20 | 0,04176337 | 0,04167379 |
| 80 | 0,04331439 | 0,04324737 |

**λ=5** resulta seleccionado en ambas ediciones **sin consultar las etiquetas 2024/25**. Es la penalización más débil de la rejilla original; no queda probado que sea óptima y **no se ampliará la rejilla retroactivamente usando el mismo holdout ya explorado**.

Los coeficientes finales \`[intercepto, pendiente inactivo, pendiente activo]\` para la primera edición son \`[-0,308463; 1,300075; 1,806742]\` y para la segunda \`[-0,335728; 1,304542; 1,892413]\`. Las pendientes positivas son compatibles con un mayor riesgo condicional cuanto mayor es la intensidad dentro de cada estado, pero no prueban causalidad ni estabilidad fuera del intervalo histórico.

### Heterogeneidad y fallos

- En la cohorte 2024 se reduce el Brier en el grupo activo al origen en **−0,01048** (37 países) y en el inactivo **−0,00184** (159 países).
- En 2025 se reduce en los activos **−0,01339** (34 países), pero **empeora +0,00050** entre inactivos (162 países). No es una mejora uniforme.
- **168 de los 196 países** presentan una reducción en el Brier medio de ambos años; **28 países** empeoran. La mejora agregada oculta errores locales importantes, por lo que no debe presentarse un mapa de países como predicciones certificadas.
- Las dos ediciones de origen comparten gran parte de sus años de entrenamiento y validación: no equivalen a dos replicaciones estadísticas independientes.

**Dictamen limitado:** se obtiene una mejora retrospectiva consistente en dos años evaluados y por encima de una calibración de intercepto. **No corresponde sustituir el modelo original ni emitir ahora la variante como sistema validado**, porque los dos años de evaluación ya se conocían al escoger esta nueva familia de modelos. La prueba necesaria sería un outcome ulterior, publicado en una edición futura, que no hubiese formado parte de ninguna decisión de investigación sobre esta arquitectura. Ningún resultado oficial 2027 se ha resuelto.

Archivos verificables: script `scripts/experiment_geo2027_log1p_nested_h2.py`, tests `scripts/test_experiment_geo2027_log1p_nested_h2.py` y reporte JSON `data/geo2027-log1p-nested-h2.json`. GitHub Actions repite todo el estudio desde fuentes con SHA oficial y compara el resultado byte a byte antes de permitir el despliegue.
