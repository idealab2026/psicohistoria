# GEO H2 · Sensibilidad del umbral cero entre tres pares consecutivos UCDP

**Investigación retrospectiva · 18/11/2026.** El resultado de Ruanda y Burundi se había estudiado principalmente con UCDP 23.1 frente a 24.1. Esta ampliación comprueba la dependencia del par de fuentes en tres transiciones: **23.1→24.1, 24.1→25.1 y 25.1→26.1**.

Para cada transición se evalúan los mismos **11 pseudo-orígenes de 2012–2022**, con objetivo dos años después (2014–2024), 196 GWNO congelados y las **etiquetas objetivo UCDP 26.1 fijas**. Son 33 combinaciones de origen y par de edición, equivalentes a 6.468 evaluaciones país-año-par. No son observaciones independientes: se repiten los países, los años y parte de las ediciones.

## Contraste predefinido

Se verifica SHA-256 de las cuatro ediciones oficiales de UCDP OrganizedViolenceCY. Se mantiene el modelo de cuatro estados, Dirichlet(1), shrinkage 20 y corte temporal para cada origen, con 199 países de aprendizaje del prior global. Las intervenciones de fuente se separan en dos bloques:

- **Z:** revisiones de recuentos históricos entre cero y 1–24 muertes, en cualquiera de ambas direcciones.
- **O:** todas las demás revisiones de recuentos históricos, incluidas variaciones dentro de una categoría y cambios entre categorías distintas de 0↔1.

Cada origen y par se reconstruye como factorial 2×2 de cuatro probabilidades `00,10,01,11`. Se calcula el Shapley simétrico de cada bloque para las probabilidades y el Brier con etiquetas 26.1. La suma debe recuperar exactamente el cambio total. Se conservan por origen las revisiones de cero a baja intensidad, su efecto sobre el estado inicial, los cinco países más sensibles, el efecto sobre el Brier y el agregado por pareja. El par 23.1→24.1 debe reproducir las 11 comparaciones de Brier ya publicadas.

## Evidencia y limitaciones

La comparación **no demuestra validez prospectiva**: estas ediciones UCDP se publicaron después de muchos de los orígenes reconstruidos y la edición 26.1 aporta a la vez algunas características de una fuente de entrenamiento y las etiquetas de evaluación. Se informa esta dependencia explícitamente. No hay selección de parámetros basada en las etiquetas de resultado, ni modificación de GEO2027/GEO2028.

La primera ejecución validada generará `data/geo-h2-three-adjacent-vintage-zero-low-11-origin.json`, cuyo contenido se fijará y revisará de nuevo en CI antes de fusionar.

## Resultados oficiales del replay

Las 33 combinaciones de pseudo-origen y par de ediciones se han reproducido desde las cuatro fuentes oficiales verificadas por SHA. Las etiquetas de resultado proceden de UCDP26.1. No se cambia la definición original del modelo.

| Par UCDP | Revisiones únicas 0↔1–24 | Pseudo-orígenes con revisión del estado inicial | Máximo efecto absoluto individual de Z | Brier medio atribuido a Z |
|---|---:|---:|---:|---:|
| 23.1 → 24.1 | 6 | 2 | 21,3549 pp (Burundi, origen 2022) | +0,000116136 |
| 24.1 → 25.1 | 1 | 1 | **22,9588 pp (Venezuela, origen 2021)** | +0,000034614 |
| 25.1 → 26.1 | 6 | 0 | 1,2958 pp (Irán, origen 2012) | −0,000016042 |

Para **Venezuela (GWNO 101)**, UCDP cambia el recuento del pseudo-origen **2021 de 0 a 1 fallecido** entre 24.1 y 25.1. Con horizonte de dos años a 2023, la probabilidad reconstruida del modelo de cuatro estados cambia de **0,054844324873** a **0,284792818584**. La atribución Shapley del bloque de umbral cero es **+0,229587848314**, una variación mayor que la de Burundi (+0,213549) y Ruanda (+0,112437) en el par anterior. Es un efecto sobre la predicción del estimador, no sobre los hechos históricos.

En el par **25.1→26.1**, los seis cruces de umbral en años pasados cambian transiciones locales/globales, pero no reclasifican el estado inicial de ninguno de los once pseudo-orígenes en los 196 países. Su mayor efecto absoluto individual de Z es **0,012958098242** en Irán (GWNO 630), con origen 2012; no demuestra que la edición 26.1 sea globalmente más estable porque está condicionada a las revisiones concretas presentes en ese par.

### Diferencia entre sensibilidad individual y desempeño agregado

El cambio total de Brier medio del modelo de cuatro estados al revisar las fuentes —incluyendo ambos bloques Z y O— fue:

| Par de ediciones | Brier nuevo menos anterior |
|---|---:|
| 23.1 → 24.1 | −0,000047753 |
| 24.1 → 25.1 | −0,000100055 |
| 25.1 → 26.1 | −0,000226797 |

Las tres diferencias medias son pequeñas y favorables a la nueva edición en **esta evaluación retrospectiva fija**, a pesar de que existen desplazamientos muy grandes en países concretos. No se infiere mayor habilidad prospectiva por una reducción retrospectiva del error.

[Informe JSON íntegro, 33 orígenes-pareja](../data/geo-h2-three-adjacent-vintage-zero-low-11-origin.json) · [Reproductor SHA](../scripts/experiment_geo_h2_three_adjacent_vintage_zero_low.py) · [Pruebas](../scripts/test_experiment_geo_h2_three_adjacent_vintage_zero_low.py).

**Restricción interpretativa:** la aparición de Ruanda, Burundi y Venezuela en distintos pares constituye una replicación del *mecanismo de sensibilidad mecánica* del estimador, no una validación independiente de que sus probabilidades históricas hayan sido buenas ni una prueba causal. Las fuentes de origen son retrospectivas y las etiquetas objetivo se reutilizan en las comparaciones.
