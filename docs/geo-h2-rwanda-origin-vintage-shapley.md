# GEO H2 — Ruanda: revisiones de su historial frente al resto del mundo

**Investigación retrospectiva · 18/11/2026.**

La auditoría anterior identificó que Ruanda (GWNO 517) tuvo el mayor cambio individual en la diferencia histórica de Brier de 2023. El modelo Markov de cuatro estados reconstruido desde UCDP 23.1 asignaba **0,159390196535** a la actividad en 2023, frente a **0,272686169101** desde UCDP 24.1. Su probabilidad aumenta en **0,113295972566** sin cambiar el algoritmo.

El presente experimento separa **dos bloques de ediciones de la fuente**, no dos mecanismos causales:

- **Ruanda:** registros propios de fallecidos UCDP 1989–2021.
- **Resto del mundo:** registros de los otros países incluidos en la fuente original (incluidos los que no pertenecen a la cohorte evaluada de 196), que también determinan la matriz de transiciones global usada para suavizar las probabilidades locales.

Se reconstruye cuatro veces el mismo estimador `4 estados, prior Dirichlet 1, shrinkage 20, H2`, con el mismo corte temporal 2021 y la misma cohorte de 196 países. Se usa UCDP 23.1 como base y se sustituyen por 24.1 solo los registros del bloque indicado.

| Ruanda | Otros 198 países de entrenamiento | Interpretación |
|---|---|---|
| 23.1 | 23.1 | Probabilidad histórica de referencia |
| 24.1 | 23.1 | Edición local solamente |
| 23.1 | 24.1 | Edición del prior global/resto solamente |
| 24.1 | 24.1 | Probabilidad histórica revisada |

Se calcula una **atribución Shapley mecánica exacta** que promedia ambos órdenes de cambio. Los efectos locales y del resto han de sumar exactamente el desplazamiento de 0,113295972566. También se enumeran los registros país-año cuyo recuento cambió y los que cruzaron algún umbral de los cuatro estados (0, 1–24, 25–99, ≥100).

**Control de calidad:** el estudio vuelve a descargar los archivos oficiales, exige su SHA-256, comprueba la cohorte y las fechas y reconstruye exactamente ambas probabilidades ya publicadas en el estudio de 2023. No atribuye a Ruanda un efecto causal sobre los coeficientes de todo el mundo.

**Limitación principal:** los archivos UCDP 23.1 y 24.1 son posteriores al origen histórico simulado 2021. Esto es un análisis de sensibilidad *ex post*, no un pronóstico emitido en 2021 ni una validación de capacidad predictiva real. No se cambia ningún resultado de GEO2027 ni GEO2028.

Informe reproducible: `data/geo-h2-rwanda-2021-23-24-source-shapley.json`. No debe afirmarse ninguna atribución local/global concreta hasta que pase la reconstrucción de GitHub Actions.

## Resultado de la reproducción oficial

Las dos fuentes contienen **199 países con registros de entrenamiento** para el análisis de transiciones globales; de ellos, **196** pertenecen a la cohorte de evaluación. Se conservan los 199 en el estimador original, sin excluir países al reconstruir el prior global.

Entre UCDP 23.1 y 24.1, restringidas al periodo anterior o igual a 2021, se identifican **93 revisiones país-año de fallecidos** y **9 reclasificaciones de los cuatro estados**. En Ruanda hubo cuatro modificaciones:

| Año | Recuento 23.1 | Recuento 24.1 | Estado |
|---|---:|---:|---|
| 1996 | 90 | 113 | 25–99 → ≥100 |
| 1997 | 980 | 985 | ≥100 → ≥100 |
| 2018 | 6 | 9 | 1–24 → 1–24 |
| 2021 | 0 | 7 | 0 → 1–24 |

### Reconstrucciones de Ruanda para el horizonte histórico 2023

| Edición de Ruanda | Edición de los otros 198 países de la fuente | Probabilidad |
|---|---|---:|
| 23.1 | 23.1 | 0,159390196535 |
| 24.1 | 23.1 | 0,273334515466 |
| 23.1 | 24.1 | 0,159351846185 |
| 24.1 | 24.1 | 0,272686169101 |

Atribución Shapley simétrica de dos bloques:
- Revisiones locales de Ruanda: **+0,1136393209235** de probabilidad.
- Revisiones de los otros 198 países de entrenamiento: **−0,0003433483575**.
- Efecto total: **+0,113295972566**, que reproduce exactamente el salto ya identificado en el análisis de 2023.
- Interacción local × resto: **−0,000609996015**. Se informa por separado; no se suma de nuevo a los efectos Shapley porque estos ya la distribuyen simétricamente.

El cambio del último estado disponible (2021: cero → baja intensidad) podría ser dominante, pero los cambios locales de 1996 y de los recuentos en 1997/2018 se han intervenido conjuntamente. **Todavía no está identificada su contribución por año**.

[Informe JSON oficial y reproducible](../data/geo-h2-rwanda-2021-23-24-source-shapley.json) · [Reproductor](../scripts/experiment_geo_h2_rwanda_origin_vintage_shapley.py) · [Pruebas](../scripts/test_experiment_geo_h2_rwanda_origin_vintage_shapley.py)

La cifra procede de ediciones históricas retrospectivas. No implica que el modelo hubiera emitido ese pronóstico en 2021.
