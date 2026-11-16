# GEO2027 LOG1P — Calibración emparejada sobre Markov global-only

**Protocolo del 16/11/2026.** Este estudio corrige una limitación de la PR #98: aquella introducía probabilidades Markov *global-only* en un calibrador logístico aprendido a partir de offsets Markov con historia nacional. Es un cambio de distribución del predictor que impedía evaluar un pipeline completo coherente.

## Diseño y corte temporal

Se mantienen los mismos **13 bloques año–edición**: nueve objetivos 2017–2025 (UCDP 26.1); 2017 con 23.1, 24.1 y 25.1; y 2024 con 25.1. Se examinan exclusivamente los **143 casos país–bloque con 1–24 muertes estatales best en el origen**, criterio que no usa el resultado posterior.

Para objetivo histórico t, su origen H2 es t−2. El calibrador solo aprende etiquetas de años u hasta t−2. Sus predictores para cada u se construyen hasta u−2, como máximo t−4. Las ediciones UCDP originales se verifican por SHA-256 y no se suponen disponibles contemporáneamente en esos años retrospectivos.

## Exclusiones de país y matched training

Sea c el país que queremos evaluar e i otro país en un ejemplo de entrenamiento. En cada origen u−2 del ejemplo de entrenamiento, se forman probabilidades de Markov global-only **excluyendo de las transiciones globales tanto a c como a i**. No se utilizan conteos locales de i. La única información de i necesaria en el Markov es su estado binario observado en u−2. Además, se **eliminan todas las etiquetas históricas de c** del ajuste logístico.

Los priors Laplace-1 para cada estado se calculan con las transiciones de todos los países j distintos de c e i, hasta ese origen. El Markov global-only H2 usa las probabilidades de dos transiciones. La regresión LOG1P con offset logit se reentrena con esos scores global-only, ridge λ=5 fijo, manteniendo la familia α=0 o α=1 sin ninguna nueva búsqueda.

Al evaluar c en t−2, el Markov global-only se construye excluyendo a c del agregado, sin sus transiciones locales, pero con **su estado binario de origen y su conteo de muertes de origen observados**. Así, el país no contribuye ni con etiquetas supervisadas ni con transiciones históricas al ajuste de su propio forecast.

## Tres protocolos comparados

- **PR #97:** Markov original con historial nacional y calibración LOG1P entrenada sin etiquetas del país evaluado.
- **PR #98:** Markov global-only sin la historia nacional del país, pero con calibrador entrenado sobre offsets Markov locales del resto, que implica posible desajuste.
- **Nuevo protocolo matched:** Markov global-only sin el país evaluado ni el país de cada fila de entrenamiento, y calibrador reentrenado sobre offsets de esa **misma familia**.

En cada diseño se calcula diferencia de Brier α1 menos α0 para países subumbrales, normalizada por el número total de países evaluables del año, y Brier **absoluto** separado para α=0 y α=1 **dentro del subconjunto 1–24**. No se presenta este último como Brier del universo de 196 países: el recalibrado en los demás casos no se evalúa aquí y este estudio mide transferencia en el grupo donde ambas variantes difieren. Se miden también cambios de signo, magnitudes de los coeficientes e influencia de países individuales.

## Resultados oficiales reproducidos

Se realizaron **143 ajustes del calibrador matched excluyendo el país objetivo**, distribuidos en 13 bloques año–edición, con nueve años diferentes de la versión 26.1. La auditoría previa de las PR #97 y #98 se reproduce como control: la comparación global-only sin recalibración coincide hasta redondeo con el estudio fuente anterior.

**Comparación Brier de la variante completa α=1**, *exclusivamente para países que partían de 1–24 muertes* en cada año:

| Objetivo (UCDP 26.1) | Países elegibles | Brier α=1 global-only **no matched** | Brier α=1 global-only **matched** | Diferencia matched − anterior |
|---|---:|---:|---:|---:|
| 2017 | 9 | 0,200589 | 0,200868 | **+0,000279** |
| 2018 | 7 | — | — | **−0,015454** |
| 2019 | 10 | — | — | **−0,014461** |
| 2020 | 13 | — | — | **−0,014020** |
| 2021 | 11 | — | — | **−0,010723** |
| 2022 | 9 | — | — | **−0,009643** |
| 2023 | 15 | — | — | **−0,004831** |
| 2024 | 15 | 0,108965 | **0,095077** | **−0,013888** |
| 2025 | 12 | **0,079639** | 0,087049 | **+0,007409** |

La recalibración matched **mejora en 7 años de 9 el Brier de α=1 dentro del subgrupo**, pero **empeora 2017 y 2025**. No hay evidencia de beneficio uniforme.

### Comparación de α=1 frente a α=0

Cada diferencia es Brier(α=1) − Brier(α=0), **normalizada sobre el universo de 196 países evaluables**, pero matemáticamente procede solo de los países de origen 1–24:

| Año | Markov original con calibrador excluyente (PR #97) | Markov global-only con calibrador antiguo (PR #98) | **Markov global-only y calibrador matched** |
|---|---:|---:|---:|
| 2017 | +0,000121 | −0,000053 | **−0,000044** |
| 2018 | −0,001041 | −0,000611 | −0,001174 |
| 2019 | −0,001055 | −0,000868 | −0,001646 |
| 2020 | −0,001918 | −0,000964 | −0,001933 |
| 2021 | −0,000237 | −0,000716 | −0,001344 |
| 2022 | −0,000283 | −0,000749 | −0,001254 |
| 2023 | −0,000611 | −0,000910 | −0,001333 |
| 2024 | −0,000821 | −0,001144 | **−0,002242** |
| 2025 | +0,000635 | +0,000093 | **+0,000531** |

**Resultado:** 0/9 cambios de signo matched frente a global-only no matched. El método original con historia nacional, en cambio, favorecía α=0 en 2017, mientras que ambos escenarios global-only favorecen α=1. Repetir 2017 en las ediciones 23.1, 24.1 y 25.1 y 2024 en 25.1 tampoco produce cambios de signo por recalibración matched (**0 de 13 bloques**).

El valor de Brier absoluto para α=0 en el grupo subumbral también cambia: en **2024**, pasa de **0,123915** a **0,124374** con matched, mientras α=1 baja de **0,108965** a **0,095077**; en **2025**, α=0 pasa de **0,078123** a **0,078375**, mientras α=1 sube de **0,079639** a **0,087049**. Así, el ajuste adecuado corrige un desajuste del pipeline, **no garantiza mejorar ambos tratamientos de la señal**.

### Dependencia de pocos casos, incluso tras la corrección

En 2017 solo 9 países cumplen la condición de 1–24 muertes; en 2024 son 15; en 2025 son 12. Sus coeficientes de intensidad inactiva cambian de forma no despreciable al pasar a entrenamiento matched, con desplazamiento absoluto medio de **0,459**, **0,802** y **0,841**, respectivamente. Estos son cambios de parámetros logísticos, no puntos porcentuales ni significación estadística.

Los casos que más contribuyen al contraste matched en 2024 incluyen **Sudán del Sur y Angola**, que superan el umbral en el año objetivo; en 2025 aparecen **Sudán del Sur, Uganda y Armenia**, con resultados heterogéneos. No se atribuye causalidad a ninguna historia política a partir de este contraste estadístico.

**Decisión:** no seleccionar este modelo como nuevo ganador a partir de estos nueve años retrospectivos, no emitir una nueva sombra y no alterar ninguno de los archivos 2027 ya congelados. La prueba proporciona una comparación científicamente mejor controlada, **no un nuevo holdout independiente**.

## Límites científicos

La reproducción de las PR #97 y #98 es condición obligatoria para aceptar resultados. Las cohortes UCDP son revisadas y se solapan; no son réplicas IID. La penalización λ=5, los alfas y el diseño de familia se examinaron después de conocer parte de estos resultados. El protocolo matched elimina un sesgo metodológico concreto, **no crea datos de confirmación prospectiva**. Este no es un pronóstico para un país completamente desconocido: utiliza estado y muertes del año de origen.

Los SHA-256 de las **196 probabilidades GEO originales**, las **196 probabilidades LOG1P de la sombra** y las **15 alertas** se comprueban y quedan intactos. No hay observaciones oficiales de 2027 ni otra emisión. GitHub Actions debe reproducir exactamente el informe usando las cuatro ediciones oficiales SHA-fijadas.

Reproductor: scripts/experiment_geo2027_log1p_matched_global_only.py. Tests: scripts/test_experiment_geo2027_log1p_matched_global_only.py. Informe: data/geo2027-log1p-matched-global-only-calibration.json.
