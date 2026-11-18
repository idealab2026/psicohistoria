# GEO H2 — Ruanda: revisiones de su historial frente al resto del mundo

**Investigación retrospectiva · 18/11/2026.**

La auditoría anterior identificó que Ruanda (GWNO 517) tuvo el mayor cambio individual en la diferencia histórica de Brier de 2023. El modelo Markov de cuatro estados reconstruido desde UCDP 23.1 asignaba **0,159390196535** a la actividad en 2023, frente a **0,272686169101** desde UCDP 24.1. Su probabilidad aumenta en **0,113295972566** sin cambiar el algoritmo.

El presente experimento separa **dos bloques de ediciones de la fuente**, no dos mecanismos causales:

- **Ruanda:** registros propios de fallecidos UCDP 1989–2021.
- **Resto del mundo:** registros de los otros países incluidos en la fuente original (incluidos los que no pertenecen a la cohorte evaluada de 196), que también determinan la matriz de transiciones global usada para suavizar las probabilidades locales.

Se reconstruye cuatro veces el mismo estimador `4 estados, prior Dirichlet 1, shrinkage 20, H2`, con el mismo corte temporal 2021 y la misma cohorte de 196 países. Se usa UCDP 23.1 como base y se sustituyen por 24.1 solo los registros del bloque indicado.

| Ruanda | Otros 195 | Interpretación |
|---|---|---|
| 23.1 | 23.1 | Probabilidad histórica de referencia |
| 24.1 | 23.1 | Edición local solamente |
| 23.1 | 24.1 | Edición del prior global/resto solamente |
| 24.1 | 24.1 | Probabilidad histórica revisada |

Se calcula una **atribución Shapley mecánica exacta** que promedia ambos órdenes de cambio. Los efectos locales y del resto han de sumar exactamente el desplazamiento de 0,113295972566. También se enumeran los registros país-año cuyo recuento cambió y los que cruzaron algún umbral de los cuatro estados (0, 1–24, 25–99, ≥100).

**Control de calidad:** el estudio vuelve a descargar los archivos oficiales, exige su SHA-256, comprueba la cohorte y las fechas y reconstruye exactamente ambas probabilidades ya publicadas en el estudio de 2023. No atribuye a Ruanda un efecto causal sobre los coeficientes de todo el mundo.

**Limitación principal:** los archivos UCDP 23.1 y 24.1 son posteriores al origen histórico simulado 2021. Esto es un análisis de sensibilidad *ex post*, no un pronóstico emitido en 2021 ni una validación de capacidad predictiva real. No se cambia ningún resultado de GEO2027 ni GEO2028.

Informe reproducible: `data/geo-h2-rwanda-2021-23-24-source-shapley.json`. No debe afirmarse ninguna atribución local/global concreta hasta que pase la reconstrucción de GitHub Actions.
