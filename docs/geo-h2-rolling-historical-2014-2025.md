# GEO H2 — Diagnóstico retrospectivo anual 2014–2025

**Fecha del diseño: 17 de noviembre de 2026. No es una validación prospectiva.**

## Pregunta

¿La ventaja observada del Markov binario frente al de cuatro estados en los dos años 2024–2025 es estable o depende de episodios históricos concretos? ¿Los resultados cambian al utilizar ediciones oficiales posteriores de UCDP?

Para responder se han fijado por adelantado **12 orígenes anuales 2012–2023**, **12 resultados anuales 2014–2025**, el **mismo horizonte H2 de dos años**, la cohorte original inmutable de **196 GWNO** y la misma función e hiperparámetros de los dos modelos. Hay **2352 observaciones país-año únicas** en la serie principal, **no 2352 observaciones estadísticamente independientes**: son los mismos países bajo crisis y perturbaciones correlacionadas.

## Diseño y límites de identificabilidad

La serie principal usa la edición UCDP **23.1** como datos de origen de los años 2012 a 2022 y la edición **25.1** como resultados de 2014 a 2024. Para el origen 2023 se utilizan **24.1** y **26.1** para observar 2025. Así, los dos casos publicados anteriormente —2022→2024 y 2023→2025— se deben reproducir **exactamente**. Todas las ediciones se verifican por SHA-256, se comprueba el conjunto original de países y no se usa ningún año posterior al origen en los cálculos de transiciones.

**Limitación crítica, no subsanable con solo recortar años:** UCDP 23.1 se publicó después de muchos de los años de origen simulados, y la edición 25.1 también incluye datos corregidos a posteriori. Aunque el entrenamiento elimine las filas de años posteriores al origen, **los valores históricos anteriores al origen pueden haber sido revisados con información posterior al resultado simulado**. Por tanto, el cálculo constituye un **diagnóstico retrospectivo de series revisadas**; no se puede denominar *walk-forward* genuinamente prospectivo, *out-of-sample* contemporáneo ni evidencia de habilidad predictiva futura.

Como control adicional, se reconstruyen los **mismos doce años y países** utilizando **24.1** en el origen y **26.1** en el resultado. Esta segunda serie **no duplica el tamaño muestral** ni proporciona doce años más de evaluación; mide exclusivamente sensibilidad a la combinación de versiones oficiales. Las diferencias de fuente de entrenamiento y de resultado se comparan sin atribuciones causales.

## Métricas y comparadores predefinidos

Para cada año se calcula Brier y log-loss de:

- Markov binario original (shrinkage 20, Laplace 1, horizonte 2).
- Markov de cuatro estados 0, 1–24, 25–99, ≥100, Dirichlet 1 y shrinkage 20.
- Markov global sin componentes individuales, del mismo modelo original.
- Prevalencia global de cinco años, calculada únicamente con observaciones hasta el origen.

La variable principal sigue siendo `sb_total_deaths_best >=25`. Como prueba de sensibilidad de **medición del resultado**, se repiten las puntuaciones con las etiquetas `low` y `high`, sin modificar las probabilidades. Los tres recuentos oficiales no siempre están ordenados. Se calculan cotas algebraicas agudas para la diferencia de Brier entre ambos modelos con cualquier etiqueta binaria permitida por las tres estimaciones. Esas cotas **no son intervalos de confianza** ni se equiparan los países a muestras IID.

Se presenta una partición descriptiva **fijada antes de mirar los resultados**: 2014–2019 frente a 2020–2025. El corte 2020 no implica ningún efecto causal atribuido a la pandemia. No se optimiza ni selecciona un modelo en estos doce años.

## Controles de reproducción

1. Las 196 probabilidades originales de GEO2027 y las quince alertas permanecen intactas; todas sus verificaciones previas siguen activas.
2. El algoritmo de cuatro estados habilita orígenes históricos solo mediante `historical_rolling_diagnostic=True`. Su interfaz original, restringida por defecto a los dos años previos 2022–2023, se preserva.
3. El replay de 2024 y 2025 es numéricamente idéntico al informe oficial retrospectivo anterior (Brier y log-loss, para baja/central/alta).
4. Las etiquetas de cada uno de los 12 años y las cuatro fuentes coinciden con la auditoría histórica SHA-verificada de 54 paneles.
5. La serie alternativa mide, entre las mismas 2352 filas, cambios de etiqueta, cambios de estado en origen y cambios de probabilidad de los modelos entre las dos selecciones de ediciones.
6. El informe JSON debe ser **idéntico byte a byte** al reconstruido desde las fuentes UCDP, lo que bloquea tanto la CI científica como la publicación institucional en Pages cuando cambia algo.

Código: `scripts/experiment_geo_h2_rolling_2014_2025.py`. Informe: `data/geo-h2-rolling-historical-2014-2025.json`.

**El objetivo no es aumentar el tamaño aparente de la muestra para justificar una significación estadística**, sino identificar debilidades temporales, casos país-año influyentes y sensibilidad a las revisiones. Los resultados deberán interpretarse como observaciones descriptivas condicionadas a las fuentes existentes, no como predicciones realmente publicadas en el pasado.

## Resultados reales reproducidos desde cuatro archivos oficiales

**Criterio principal:** menor Brier implica menor error histórico en la codificación UCDP de los resultados. Los datos de entrenamiento previos a la fecha simulada *también* pueden estar revisados a posteriori: esta sección es descriptiva, no una prueba prospectiva.

| Modelo, 2014–2025 | Brier conjunto (2.352 país–año) |
|---|---:|
| Markov cuatro estados | **0,04416943** |
| Markov binario original | 0,04674511 |
| Markov global, sin ajuste por país | 0,05349908 |
| Prevalencia global de cinco años | 0,14335215 |

El Brier de cuatro estados es menor que el original por **0,00257568** unidades. El log-loss conjunto también favorece a cuatro estados: **0,16246205 frente a 0,17616664**.

### Variación anual

La tabla es una descripción de los **mismos 196 países cada año**, sin intervalos de confianza ni atribución causal. Δ = Brier de cuatro estados menos Brier binario.

| Año del resultado | Activos best | Brier binario | Brier cuatro estados | Δ |
|---|---:|---:|---:|---:|
| 2014 | 31 | 0,054698 | **0,046501** | −0,008197 |
| 2015 | 34 | 0,057393 | **0,053202** | −0,004191 |
| 2016 | 36 | **0,057799** | 0,058175 | +0,000376 |
| 2017 | 32 | 0,035617 | **0,033248** | −0,002369 |
| 2018 | 33 | 0,054676 | **0,053452** | −0,001224 |
| 2019 | 33 | 0,055599 | **0,048093** | −0,007506 |
| 2020 | 35 | **0,031575** | 0,032057 | +0,000482 |
| 2021 | 32 | 0,036143 | **0,031764** | −0,004379 |
| 2022 | 37 | 0,058393 | **0,050041** | −0,008352 |
| 2023 | 34 | 0,038882 | **0,038604** | −0,000277 |
| 2024 | 35 | **0,041431** | 0,046278 | +0,004847 |
| 2025 | 34 | 0,038737 | **0,038620** | −0,000116 |

Resultado descriptivo: cuatro estados presenta menor Brier en **9 de 12 años**. En el corte prefijado 2014–2019, el Brier es **0,04877821** para cuatro estados y **0,05263022** para binario; en 2020–2025, **0,03956064** frente a **0,04086000**. Ninguno de estos cortes proporciona inferencia de significación.

### Sensibilidad a la medición de fallecimientos

En el conjunto de los doce años, la diferencia Brier (cuatro estados menos original) es **−0,00300755** usando `low>=25`, **−0,00257568** usando `best>=25`, y **−0,00248160** usando `high>=25`.

El intervalo algebraico agudo con todas las clasificaciones binarias ambiguas permitidas por las tres estimaciones es **[−0,00411879, −0,00137036]**. No cruza 0. Por consiguiente, para **estas predicciones y estas observaciones retrospectivas**, la ventaja descriptiva de cuatro estados no se explica exclusivamente por la elección de `low`, `best` o `high`. Esta propiedad **no equivale a un intervalo estadístico de confianza ni a reproducibilidad con nuevos años**.

### Sensibilidad a revisiones entre ediciones

Al calcular de nuevo **los mismos 2.352 país–año** con la pareja de ediciones alternativa 24.1→26.1, el Brier binario es **0,04636564** y el de cuatro estados **0,04378973** (diferencia **−0,00257591**). La etiqueta binaria central se modifica en **una sola observación país-año**, mientras que las probabilidades de alguno de los dos modelos cambian en **2.156 de las 2.352 observaciones** debido a los historiales revisados. Las dos series **no son muestras independientes** y no pueden sumarse para aparentar 4.704 observaciones nuevas.

### Consecuencia científica

En el estudio histórico 2024–2025, el original ganaba por **+0,00236527** de diferencia Brier. Al examinar 2014–2025, el de cuatro estados obtiene una ventaja de **−0,00257568**. Por tanto, **es incorrecto extrapolar la victoria en los dos años finales a todo el período revisado**.

Sin embargo, también sería incorrecto interpretar esta inversión como evidencia ex ante de que cuatro estados predice mejor. La edición 23.1, empleada como fuente de orígenes históricos 2012–2022, no estaba disponible para la mayoría de esos orígenes. Los metadatos y variables retrospectivamente reconstruidos pueden haber incorporado conocimiento posterior. Para afirmar capacidad predictiva histórica con evidencia temporal fuerte será necesario recopilar **ediciones UCDP contemporáneas a cada origen**, registrar sus hashes y examinar la integridad del esquema de medición. Hasta entonces, la frase correcta es *mayor estabilidad descriptiva de cuatro estados en la serie histórica reconstruida, no superioridad predictiva prospectiva demostrada*.

## Fuentes

[UCDP OrganizedViolenceCY](https://ucdp.uu.se/downloads/), cuatro archivos oficiales 23.1, 24.1, 25.1 y 26.1, con sus hashes fijados en el repositorio. IDEA LAB mantiene separación institucional respecto a cualquier repositorio o identidad personal.
