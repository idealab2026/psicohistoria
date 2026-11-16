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

## Límites científicos

La reproducción de las PR #97 y #98 es condición obligatoria para aceptar resultados. Las cohortes UCDP son revisadas y se solapan; no son réplicas IID. La penalización λ=5, los alfas y el diseño de familia se examinaron después de conocer parte de estos resultados. El protocolo matched elimina un sesgo metodológico concreto, **no crea datos de confirmación prospectiva**. Este no es un pronóstico para un país completamente desconocido: utiliza estado y muertes del año de origen.

Los SHA-256 de las **196 probabilidades GEO originales**, las **196 probabilidades LOG1P de la sombra** y las **15 alertas** se comprueban y quedan intactos. No hay observaciones oficiales de 2027 ni otra emisión. GitHub Actions debe reproducir exactamente el informe usando las cuatro ediciones oficiales SHA-fijadas.

Reproductor: scripts/experiment_geo2027_log1p_matched_global_only.py. Tests: scripts/test_experiment_geo2027_log1p_matched_global_only.py. Informe: data/geo2027-log1p-matched-global-only-calibration.json.
