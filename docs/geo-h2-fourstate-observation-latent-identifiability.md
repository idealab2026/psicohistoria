# GEO H2 — Proceso de observación de cuatro estados y límites de identificabilidad

**Diseño previo a ver los resultados — 18/11/2026.**

## Problema científico

Los estudios de Ruanda, Burundi y Venezuela muestran saltos grandes de probabilidad cuando una edición de UCDP reclasifica el año de origen entre cero muertes y 1–24. Los comparadores del 10% y de frecuencias de revisión editorial ya publicados no mejoraron el Brier histórico.

Es crucial distinguir:
- **Estado real latente T:** intensidad histórica verdadera, no observada directamente.
- **Estado observado Oᵛ:** intensidad registrada por una edición concreta v de UCDP.
- **Revisión editorial Oᵛ→Oᵛ⁺¹:** transición observable entre ediciones, que **no demuestra** que Oᵛ⁺¹ sea el estado real.

Una cadena de ediciones de la misma institución no proporciona evaluadores independientes ni una muestra de referencia etiquetada con el estado verdadero. Por tanto, una matriz **P(T|Oᵛ)** no está identificada estadísticamente con estos datos.

## Modelo de revisión medible

Se estima una matriz 4×4 `P(O_later=t | O_earlier=s)` sobre los cuatro estados [0, 1–24, 25–99, ≥100]. Se conservan 199 países fuente con emparejamiento por GWNO y año, sin imputar como cero los registros ausentes.

El protocolo se fija antes de ver las puntuaciones:

- Entrenamiento: **UCDP23.1→24.1 y 24.1→25.1**, con años fuente hasta 2021 inclusive.
- Par reservado: **UCDP25.1→26.1**, mismos años históricos, evaluado como revisión de registro y **no** como verdad latente.
- Regularización: **Dirichlet(0,5) por celda** en cada fila de la matriz observada. No se ajusta con las etiquetas de conflicto del horizonte H2.
- Métricas de validación: log-loss multinomial y Brier multicategoría para el **estado registrado en la edición reservada**, más matrices completas de confusión y desglose por estado y periodo histórico.
- Control adicional: cuatro ediciones de un mismo país-año, discrepancias persistentes frente a reversión a una categoría anterior. Una reversión es evidencia de inestabilidad editorial, **no** una etiqueta auténtica del estado real.

El par reservado comparte parte de las mismas observaciones históricas y una edición intermedia con el entrenamiento; por ello, tampoco ofrece replicación completamente independiente.

## Identificación parcial y escenario de incertidumbre

Si no se conoce `P(T|O)`, el pronóstico H2 para estado verdadero T desconocido está dentro del **casco convexo de las cuatro probabilidades condicionales del Markov original**:

`min_s P(Y_H2|T=s) ≤ P(Y_H2) ≤ max_s P(Y_H2|T=s)`.

Esa banda amplia sí es válida sin hipótesis adicionales sobre el estado inicial, manteniendo fijo el proceso de transición original.

Se informa *separadamente* de una banda estrecha cuya validez depende del siguiente supuesto no verificado: cuando el registro es cero o baja intensidad, entre 0 y 10% de la masa latente puede corresponder al estado contiguo; para los estados 2 y 3 el supuesto fija certeza. La banda resultante **no es un intervalo de confianza, ni un posterior calibrado**. El límite 10% procede del escenario anterior para permitir una comparación honesta; no se optimiza con etiquetas de 2027.

## Nueva sombra independiente de 2027

Se calcula una nueva colección de **196 probabilidades** para objetivo 2027, origen 2025, a partir de UCDP26.1 con corte de entrenamiento 2025. La matriz **editorial** 4×4, estimada antes de conocer resultados de 2027, se aplica a las cuatro probabilidades H2 condicionales como **heurística de sensibilidad**, NO como distribución posterior de estado real. Se comparan valores con el Markov duro original, la sombra fija de 10% y la sombra editorial de dos estados ya registradas, cuyos ficheros no se editan.

Se almacenan por país la mezcla editorial, las cuatro probabilidades condicionales, la banda sin supuestos y la banda de máximo 10% bajo supuestos. Estas nuevas probabilidades **no sustituyen las emitidas para GEO2027 y GEO2028**, ni constituyen evidencia de mejora predictiva hasta disponer del resultado futuro.

## Condiciones de aprobación

SHA-256 de las cuatro ediciones oficiales, 199 países en el prior global, cohorte fija de 196 países, corte temporal sin fuga, reproducción exacta del modelo y las sombras 2027 anteriores, pruebas del caso de reversión, evaluación reservada y auditoría pública institucional de privacidad. El informe numérico definitivo `data/geo-h2-fourstate-observation-kernel-latent-bounds-2027.json` se fija después de la primera ejecución de CI; se publica solo tras nueva reproducción.

## Resultados reproducidos

La auditoría SHA de UCDP23.1, 24.1, 25.1 y 26.1 sobre los **6.348 mismos país-años históricos** (años ≤2021) muestra que **6.326** mantuvieron su misma categoría de intensidad en las cuatro ediciones. Hubo **22** país-años con al menos una reclasificación 4-state y **20** con discrepancia entre primera y última edición. No se observó ninguna reversión inmediata A→B→A de categoría en estos registros. Esto **no convierte** la edición final en verdad histórica.

### Matriz empírica del entrenamiento

Cada fila corresponde al estado registrado en la edición anterior y cada columna al estado en la siguiente. La tabla combina las ediciones **23.1→24.1 y 24.1→25.1**; aún no aplica los pseudoconteos Dirichlet de la matriz de probabilidades.

| Estado anterior | Nuevo 0 | Nuevo 1 (1–24) | Nuevo 2 (25–99) | Nuevo 3 (≥100) |
|---|---:|---:|---:|---:|
| 0 | 10.076 | 6 | 1 | 0 |
| 1 | 0 | 607 | 4 | 0 |
| 2 | 0 | 0 | 565 | 2 |
| 3 | 0 | 1 | 0 | 1.434 |

Se estima de esta matriz un kernel estocástico de **próxima edición registrada** mediante Dirichlet(0,5). Nunca se interpreta como una matriz de errores del estado histórico real.

### Contrastación fuera del par de ediciones de entrenamiento

El par reservado **25.1→26.1** muestra **10 cambios entre estados en 6.348 exposiciones** (0,1575 %). Las tasas observadas de cambio de categoría no son uniformes:

| Estado inicial | Tasa de cambio prevista por kernel | Tasa observada en par reservado |
|---|---:|---:|
| 0 fallecidos | 0,0843 % | 0,0794 % |
| 1–24 fallecidos | 0,8972 % | 1,3072 % |
| 25–99 fallecidos | 0,6151 % | 0,6969 % |
| ≥100 fallecidos | 0,1740 % | 0 % |

Sobre las **cuatro clases registradas**, el *log-loss* multinomial medio en el par reservado es **0,0119531** y el Brier multicategoría medio **0,00313734**. La escasez de revisiones y las dependencias entre ediciones impiden afirmar calibración estadística robusta o independencia de la muestra.

### Identificación parcial: ilustración con dos países

Para la nueva sombra 2027 calculada con UCDP26.1, el Markov original se mantiene inalterado. El kernel de revisión genera una probabilidad experimental adicional, distinta de la del 10% fijo y distinta de la sombra editorial binaria anterior.

| GWNO | Riesgo H2 estado registrado | Sombra kernel editorial 4×4 | Banda latente sin supuestos | Banda con supuesto de ≤10 % de masa 0↔1 |
|---|---:|---:|---|---|
| 2 | 4,5388 % | 4,5652 % | [4,5388 %, 74,4998 %] | [4,5388 %, 6,9253 %] |
| 517 | 23,9089 % | 24,1780 % | [16,0738 %, 68,9131 %] | [23,1254 %, 23,9089 %] |

La banda sin supuestos es amplia **porque el estado verdadero no está identificado**. La banda pequeña no es un intervalo de confianza: exige la hipótesis no verificada de masa contigua máxima de 10%, además de estados 2/3 exactos. La sombra del kernel puede quedar **fuera de la banda estrecha**, ya que modela transiciones editoriales entre los cuatro estados, no se limita a la vecindad 0↔1.

[Informe JSON completo, matrices, reservas y 196 sombras](../data/geo-h2-fourstate-observation-kernel-latent-bounds-2027.json) · [Script de reconstrucción](../scripts/experiment_geo_h2_fourstate_observation_identifiability.py) · [Pruebas](../scripts/test_experiment_geo_h2_fourstate_observation_identifiability.py).

### Decisión científica

El kernel de próxima edición está estimado y se puede contrastar con un par reservado, pero **no estima P(estado verdadero | estado registrado)**. Esta última magnitud requeriría una referencia independiente, supuestos de independencia condicional contrastables o un diseño de medición adicional. Sin tal información, un modelo latente aparentemente más preciso podría esconder parámetros imposibles de identificar.

Este avance no justifica sustituir el H2 original ni elegir pesos con resultados retrospectivos; permite registrar escenarios prospectivos separados y comunicar cuándo un intervalo procede de datos y cuándo de supuestos.
