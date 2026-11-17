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

## Fuentes

[UCDP OrganizedViolenceCY](https://ucdp.uu.se/downloads/), cuatro archivos oficiales 23.1, 24.1, 25.1 y 26.1, con sus hashes fijados en el repositorio. IDEA LAB mantiene separación institucional respecto a cualquier repositorio o identidad personal.
