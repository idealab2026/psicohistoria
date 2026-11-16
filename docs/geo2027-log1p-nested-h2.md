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

Archivos verificables: script `scripts/experiment_geo2027_log1p_nested_h2.py`, tests `scripts/test_experiment_geo2027_log1p_nested_h2.py` y reporte JSON `data/geo2027-log1p-nested-h2.json`. GitHub Actions repite todo el estudio desde fuentes con SHA oficial y compara el resultado byte a byte antes de permitir el despliegue.
