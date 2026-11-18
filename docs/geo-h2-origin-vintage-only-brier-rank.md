# GEO H2 — La revisión del origen modifica el ranking en 2023

**Estudio retrospectivo, 18 de noviembre de 2026.** Dos factores suelen mezclarse cuando cambian las ediciones de UCDP: el historial usado para reconstruir las probabilidades y los datos usados para evaluar las etiquetas. Este experimento los descompone manteniendo fija la edición de resultado **26.1** y alternando exclusivamente la edición de entrenamiento **23.1 → 24.1**, con idéntico año de origen y algoritmo.

## Diseño factorial reconstruido

| Reconstrucción | Fuente del origen | Etiquetas del objetivo |
|---|---|---|
| A: serie histórica original | 23.1 | 25.1 |
| B: cambio **solo de evaluación** | 23.1 | 26.1 |
| C: cambio **solo de origen** respecto de B | 24.1 | 26.1 |

Por álgebra de puntuaciones, `C − A = (B − A) + (C − B)`. Se combinan dos experimentos **ya reproducidos y con fuentes UCDP SHA verificadas**. No se retoca una sola probabilidad prospectiva.

Cohorte de **196 países × 11 años objetivo 2014–2024 = 2.156 pares**. No incluir 2025: para ese año el estudio rolling anterior ya utiliza 24.1 como origen de la serie primaria, lo que haría que ambos orígenes fueran idénticos.

## Hallazgo

El cambio de origen produce **1 inversión del ganador en 11 años**, exclusivamente en el año objetivo **2023**:

| Edición de origen, objetivo 2023 | Markov 4 estados menos binario, Brier | Ganador |
|---|---:|---|
| 23.1, etiquetas 26.1 | −0,0002771979 | Cuatro estados |
| 24.1, etiquetas 26.1 | +0,0000349581 | Binario |

Es una inversión de margen estrechísimo: la diferencia entre modelos cambia en **+0,00031215598 unidades Brier** al revisar el origen, sin modificar la edición de evaluación ni el periodo.

En el agregado de 11 años **no** hay inversión: cuatro estados mantiene la mejor puntuación. Las variaciones globales de Brier al cambiar solo la fuente de origen fueron:

| Modelo | `Brier_origen24.1 − Brier_origen23.1`, objetivo 26.1 |
|---|---:|
| Binario | −0,0000864384 |
| Cuatro estados | −0,0000477529 |
| Markov global | +0,0000094068 |
| Prevalencia quinquenal | 0 |

El análisis anterior de revisión **solo del objetivo** 25.1→26.1 daba **0 cambios de ranking anual**. Esta nueva inversión muestra que la estabilidad frente a cambios de etiquetas no implica necesariamente estabilidad frente a cambios del historial de origen.

## Alcance y límites

Las fechas de publicación de 23.1 y 24.1 son posteriores a muchas fechas de los supuestos orígenes 2012–2022. No existen aquí emisiones históricas genuinas fechadas antes de esos objetivos. Tampoco puede inferirse qué observación concreta del historial explica el cambio en 2023: variar la edición de origen puede alterar muchos registros y probabilidades simultáneamente. El experimento aísla el **efecto conjunto** de revisar la fuente de entrenamiento, no una atribución causal por variable.

Los 11 años y los países son dependientes; no se calcula significación ni se proclama habilidad predictiva futura.

## Artefactos

- [Tabla auditada con los tres escenarios por año y todos los modelos](../data/geo-h2-origin-vintage-only-brier-rank.json)
- [Recálculo y controles de procedencia](../scripts/audit_geo_h2_origin_vintage_only_brier_rank.py)
- [Pruebas de inversión y controles negativos](../scripts/test_audit_geo_h2_origin_vintage_only_brier_rank.py)

**Siguiente contraste falsable:** para el origen 2021 y objetivo 2023, reconstruir las probabilidades país por país de ambos modelos y descomponer los cambios de Brier sobre exactamente las mismas etiquetas 26.1, para descubrir si el cambio proviene de pocos países de alta influencia o de una diferencia distribuida. No utilizar resultados de 2023 para reajustar los modelos.
