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
