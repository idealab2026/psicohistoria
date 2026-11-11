# GEO-2027 — ¿Se pueden priorizar alertas de cambios de estado?

**Diagnóstico de clasificación retrospectiva ex post, 11 de noviembre de 2026.** No forma parte de la emisión prospectiva para 2027 ni presupone conocer resultados de 2027.

## Estimando de alerta y cohortes

Para evitar que la mera continuidad de conflictos domine el Brier agregado, separaremos **antes de observar el resultado** los países según su estado en el año de origen:

- **Entrada 0→1:** países que estaban por debajo del umbral de **25 muertes por violencia estatal organizada** en el origen. Etiqueta 1 si superan ese umbral en el objetivo a **dos años**.
- **Resolución 1→0:** países que estaban por encima del umbral en el origen. Etiqueta 1 si están por debajo en el objetivo. Una resolución del umbral no certifica un acuerdo de paz ni el fin político de una guerra.

El objetivo es el mismo `sb_total_deaths_best >=25` de UCDP OrganizedViolenceCY, **no** la primera aparición de un conflicto (`newconf`) ni `onset2`. La clasificación de cada riesgo está disponible al origen.

Usamos exactamente los dos holdouts con fuentes separadas y SHA-256 previamente auditados: **23.1 (origen 2022) → 25.1 (objetivo 2024)** y **24.1 (origen 2023) → 26.1 (objetivo 2025)**. El universo está fijado a 196 países por año, 392 observaciones, 69 casos con estado positivo; el estudio anterior verificó **8 entradas** y **10 resoluciones**. Solo se incorporan las etiquetas de los años objetivo de las ediciones posteriores; no se recalculan modelos, umbrales ni predicciones originales.

## Comparadores cerrados

`country_markov`: el modelo nacional de Markov de dos pasos ya congelado. `global_markov`: el Markov global del mismo protocolo (referencia dentro de cada estado de origen). Para cada país con estado originario 0, el riesgo de entrada es `p_model` o `p_global_markov`. Para estado originario 1, el riesgo de resolución es `1-p_model` o `1-p_global_markov`.

La comparación se realiza **dentro de cada conjunto de riesgo ex ante**, globalmente y por cada año objetivo.

Evaluaremos únicamente:

- **Brier condicional**, junto con media de riesgo prevista y prevalencia observada.
- **ROC AUC** con medio crédito para pares empatados.
- **Área escalonada de precisión–recobrado por grupos de empates**, sin convertirla en *average precision* secuencial dependiente del orden arbitrario de países.
- **Capacidad fija de alertas:** 10 entradas potenciales y 5 resoluciones potenciales por conjunto de riesgo (por año y, separadamente, total). Si un empate cruza la frontera, se publica el **intervalo mínimo–máximo de aciertos**, nunca un valor elegido alfabéticamente.
- Diferencia de Brier frente al Markov global, más bootstrap determinista agrupado por país para los conjuntos de riesgo agrupados (sensibilidad únicamente: no recoge shocks globales).

Se rechazarán cohortes incompletas, etiquetas inesperadas, hashes distintos, cambios en los 392 casos y discrepancias frente al Brier del informe de atribución previo.

## Criterios de aceptación y limitaciones

No se seleccionarán umbrales después de examinar los resultados ni se buscarán presupuestos de alertas alternativos hasta obtener aciertos aparentes. **Cuatro entradas por año** y cuatro/seis resoluciones suponen una potencia estadística extremadamente pequeña; es posible no detectar ninguna señal operativa útil.

Una AUC alta o una mejora numérica de Brier en estas ediciones puede ser compatible con sobreajuste o cambio de cobertura histórica. Las fuentes no cuentan con notarización independiente de la fecha histórica de disponibilidad. El dato de los años objetivo fue inspeccionado antes de diseñar este experimento: **es post hoc, no confirmatorio**.

El informe solo publica **agregados por riesgo y año**, no identificadores de país, pronósticos individuales, nombres, etiquetas individuales ni datos personales. Los pronósticos **GEO-2027 y NEWCONF-2027**, sus SHA, manifiestos, primeras fechas públicas, protocolos y decisiones originales permanecen inmutables.

Un modelo útil para decisiones debe demostrar capacidad de priorizar entradas/resoluciones **frente a referencias en conjuntos conocidos al origen**. Si no lo consigue, la decisión es registrar el fallo y evitar afirmaciones de habilidad predictiva sobre nuevos conflictos.

## Resultados reproducidos con ediciones originales UCDP

CI de GitHub ha ejecutado el experimento original completo y ha comparado los cuatro SHA-256 con los archivos oficiales. El resultado agregado exacto se conserva en `data/geo2027-transition-alert-ranking-archival.json`. El mismo script se ejecuta en las siguientes auditorías y falla si cambia un solo byte.

| Riesgo en el origen | País-años | Transiciones observadas | AUC nacional | Área PR nacional con empates | AUC global |
|---|---:|---:|---:|---:|---:|
| Entrada (origen 0) | 321 | 8 | **0.87141** | **0.18126** | 0.50240 |
| Resolución (origen 1) | 71 | 10 | **0.75820** | **0.37272** | 0.54590 |

La AUC global supera 0.5 en el conjunto agrupado porque las probabilidades globales pueden variar **entre los dos años objetivo**, aunque no discriminan entre países dentro del mismo estado/año. No debe compararse con una predicción de fechas aleatorias.

**Capacidad de alertas fijada previamente:**

- **Entrada:** las 10 probabilidades nacionales más altas capturan **3 de 8 entradas** en las 321 evaluaciones combinadas (30 % de precisión sobre diez alertas); la selección no presenta empate en el corte. Desagregado por año con 10 alertas en cada uno: **2 de 4** entradas de 2024 y **1 de 4** de 2025. La esperanza de aciertos a azar entre 10 casos agrupados sería **0.25** (mismo universo, no prueba formal de independencia ni significación).
- **Resolución:** las 5 probabilidades nacionales más altas capturan **2 de 10 resoluciones** en el conjunto combinado (40 % de precisión); por año, **2 de 6** resoluciones en 2024 y **2 de 4** en 2025 usando cinco alertas anuales.
- **Markov global:** varios países empatan en la frontera de alertas y **no existe un top-k único**: el script publica intervalos mínimo–máximo de aciertos compatibles con cada empate. Un resultado top-k elegido arbitrariamente entre países empatados no constituye ventaja predictiva.
- Brier condicional de entradas: nacional **0.02264753**, global **0.02521028**. Su intervalo bootstrap por país para (nacional−global) es **[-0.00721, +0.00066]**, que incluye cero.
- Brier condicional de resoluciones: nacional **0.11891681**, global **0.14507856**. Su intervalo descriptivo bootstrap por país es **[-0.03949, -0.01276]**, pero no recoge correlaciones por shocks comunes.
- **Calibración por origen:** entre inactivos el modelo pronostica entrada con riesgo medio **4.21 %** frente a **2.49 %** observado; entre activos pronostica resolución con riesgo medio **23.34 %** frente a **14.08 %** observado. Ambas transiciones aparecen **sobreestimadas**. La buena discriminación retrospectiva no implica probabilidades correctamente calibradas.

### Lectura científica

Los datos ofrecen **una señal retrospectiva de discriminación** más interesante que el Brier global de GEO: el score nacional concentra algunas transiciones en pocas alertas. Pero el objetivo y el examen histórico son **post hoc** y solo abarcan 8 y 10 casos, dos años y ediciones sin fecha de publicación originaria notariada. AUC elevada, selección fija y pequeñas diferencias Brier **no certifican utilidad operativa prospectiva**.

**Decisión:** conservar íntegramente los vectores prospectivos GEO-2027 y NEWCONF-2027, sin reentrenar ni ajustar umbrales a estos resultados. Para una futura cohorte nueva se necesitan origen, horizonte, presupuestos de alerta, función de costes, comparadores y fuente de resultado registrados antes del objetivo. Los indicadores de entrada y resolución no se equiparan a aparición de nuevos conflictos, `newconf` o `onset2`.
