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
