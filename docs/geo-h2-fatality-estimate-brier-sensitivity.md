# GEO H2 — Robustez retrospectiva a estimaciones de fallecidos UCDP

**Diseño preespecificado el 17/11/2026.** Prueba de sensibilidad posterior al estudio de modelos originales, no nueva emisión de predicciones. Ningún dato oficial de 2027 se conoce. Este experimento tiene como objetivo evaluar la **dependencia de los resultados históricos** de la forma concreta de codificar víctimas en UCDP OrganizedViolenceCY.

## Hipótesis y comparación estricta

Se enfrentan, sin reajuste ni selección de parámetros:

1. **Markov binario original:** dos estados (fallecimientos estatales UCDP `best <25` / `best>=25`), Laplace 1 y *shrinkage* 20. Probabilidades recalculadas con la misma función de entrenamiento histórica del modelo original.
2. **Markov de cuatro estados:** 0; 1–24; 25–99; >=100, Dirichlet(1) global y *shrinkage* 20, configuración ya registrada en el estudio de ablación original.

Origen **2022, edición oficial 23.1** → resultado **2024, edición 25.1**, y origen **2023, edición 24.1** → resultado **2025, edición 26.1**. Horizonte fijo de dos años. Los mismos 196 GWNO se evalúan en cada bloque; **392 filas país×año, pero únicamente dos años objetivo que comparten países**. Las predicciones solo utilizan la edición de origen y datos hasta el año de origen.

La puntuación primaria del backtest continúa siendo el Brier con `sb_total_deaths_best >=25`. Los tres **escenarios secundarios de medición** sustituyen la etiqueta de destino por `low>=25`, `best>=25` o `high>=25` **sin tocar ni una probabilidad generada**.

El signo reportado es:

`Δ Brier = Brier(Markov cuatro estados) − Brier(Markov binario original)`

Δ positivo favorece al original; Δ negativo favorece a cuatro estados. Se calculan Brier y log-loss por bloque y conjuntamente. No se buscará otro umbral favorable ni se escogerá el estimador de víctimas que dé mejor puntuación.

## Identificación parcial de la ventaja entre modelos

Para cada país-año del conjunto de evaluación, se toma el conjunto de etiquetas binarias observado entre las **tres estimaciones oficiales**. Si todas coinciden, la etiqueta queda fija; si divergen, se admite 0 o 1. El mínimo y máximo algebraico de

`[(p_4−y)²−(p_original−y)²]`

sumados sobre las filas y divididos por 196 (bloque) o 392 (conjunto) constituyen **cotas agudas de sensibilidad de la diferencia de Brier**, bajo asignaciones binarias individuales a las filas ambiguas.

**Advertencias:** estas cotas **no son intervalos de confianza**, ni bandas de predicción, ni demuestran que el escenario conjunto de extremos sea físicamente alcanzable. No se asume independencia de países o años. Las estimaciones oficiales `low,best,high` pueden **no estar ordenadas numéricamente**, fenómeno real verificado en la edición 26.1, por lo que el conjunto se obtiene de las **tres etiquetas**, nunca de suposiciones como `low<=best<=high`.

## Auditoría de integridad

- **Cuatro archivos originales** oficiales, cada uno con SHA-256 y total de filas contrastados previamente en el proyecto.
- Contraste país–año de cada triple contra `best` leído por el parser original. Cualquier observación ausente provoca un fallo; no se imputa ausencia de violencia.
- Reproducción numérica (tolerancia 1e−10) de los Brier y log-loss originales en cada bloque contra los informes **ya publicados**, además de su puntuación conjunta.
- Conciliación del número de países activos en `low,best,high` y del conjunto exacto de GWNO ambiguos con la auditoría de 54 paneles de la PR #106.
- Pruebas con etiquetas sintéticas, inversiones de orden en los recuentos, exactitud del Brier, cotas comparadas por enumeración exhaustiva y ausencia de *leakage* después del origen.
- Una puerta adicional en la publicación de GitHub Pages exige que el informe sea **idéntico byte a byte** al reconstruido desde las fuentes.

**Fuente del cálculo:** `scripts/experiment_geo_h2_fatality_estimate_brier_sensitivity.py`. **Resultados científicos reproducibles:** `data/geo2027-h2-fatality-estimate-brier-sensitivity.json`.

## Interpretación previa a los resultados

El informe archivado de cuatro estados registra la ventaja conjunta del modelo binario de **0,00236527** puntos Brier con `best>=25`; para 2024 la ventaja binaria es **0,00484688**, mientras que para 2025 la alternativa de cuatro estados aventaja en **0,00011634**. El objetivo de esta prueba es determinar si las pocas filas cuya clasificación depende de la estimación de fallecidos alteran el signo de estas diferencias; no estimar capacidad predictiva ex ante.

**Limitación temporal:** esta reconstrucción de archivos es *ex post*; las predicciones históricas no fueron publicadas bajo una prueba de fecha fiable antes de conocer los resultados. No puede utilizarse para afirmar un acierto prospectivo de PSICOHISTORIA. Las predicciones GEO2027/GEO2028 originales y las alertas permanecen congeladas. Todo el estudio se publica bajo IDEA LAB sin referencias a repositorios privados ni identidades personales.

## Fuentes

[UCDP OrganizedViolenceCY](https://ucdp.uu.se/downloads/) y [codebook 26.1](https://ucdp.uu.se/downloads/organizedviolencecy/UCDP_OrganizedViolenceCY_Codebook_261.pdf). Consulte los SHA-256 fijados y el diseño de las dos cohortes en los informes históricos del repositorio.
