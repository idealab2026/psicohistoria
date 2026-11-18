# GEO H2 — Frecuencias empíricas de revisión de la categoría inicial

**Protocolo previo a resultados · 18/11/2026.**

## Problema

La sombra anterior imponía una probabilidad **10%** de que la categoría del origen 0 o 1 fuera la contigua. Reducía ligeramente la inestabilidad entre ediciones, pero empeoraba el Brier histórico. No existe evidencia de que el 10% represente el error real del recuento.

## Regla y separación de ediciones

Se miden las **frecuencias de reclasificación editorial**, separadas por categoría observada, en ediciones consecutivas oficiales UCDP:

- Entrenamiento: **23.1→24.1** y **24.1→25.1**; país-años de 1989 a **2021** y cobertura común de los 199 países de origen.
- Reserva para evaluación de la tasa de revisión: **25.1→26.1**, mismos años históricos.
- Denominadores: todos los país-años cuyo estado en la edición antigua era 0 o 1, *incluidos los que no fueron revisados*.
- Numeradores: cambios de categoría **0→1** o **1→0**; no se incluyen otras reclasificaciones.
- Suavizado congelado antes de evaluar: posterior medio de una tasa binomial con prior de **Jeffreys Beta(0,5; 0,5)**. La frecuencia ajustada es `(cruces + 0,5)/(exposiciones + 1)`.

El par reservado mide únicamente si estas frecuencias predicen **la siguiente revisión editorial**; no si el estado registrado era verdadero ni la tasa de clasificación errónea. Las observaciones país-año se repiten entre pares y no son independientes. No se infieren intervalos frecuentistas independientes de esa muestra.

## Comparador con mezclas de estados

Se reutiliza *exactamente* la matriz de cuatro transiciones y la probabilidad a dos años del Markov original. Si el estado inicial registrado es 0, se asigna una pequeña masa al 1 igual a la frecuencia editorial estimada de **0→1**; si es 1, se utiliza la tasa estimada de **1→0**. Para 2 y 3 no se altera la clasificación. **Esta mezcla es una heurística anclada en revisiones**, no una probabilidad identificada de estado latente verdadero.

Se publicarán dos análisis explícitamente distintos:

1. **Diagnóstico retrospectivo 2012–2022**, usando UCDP 23.1/24.1 de origen y etiquetas 26.1 fijas para el objetivo H2 2014–2024. Es una reconstrucción recortada temporalmente; las ediciones publicadas posteriormente contaminan la interpretación *as-of*. No sirve para afirmar habilidad predictiva prospectiva.
2. **Nueva emisión sombra independiente 2027**, origen 2025, fuente oficial 26.1, 196 GWNO. Las tasas quedan fijadas usando solo las ediciones disponibles y el protocolo declarado. No se sustituye ninguna emisión GEO2027/GEO2028 ya publicada. Es imprescindible preservar fecha/commit inicial del vector antes de conocer etiquetas de 2027.

## Auditoría

Los archivos oficiales tienen SHA-256 comprobado; cobertura anual estricta y sin imputación de cero, horizonte 2 años, 199 países de entrenamiento, 196 evaluados, reproducción de probabilidades de origen históricas, pruebas sintéticas y auditoría pública de privacidad. Ningún peso puede seleccionarse por el Brier de los datos objetivo.

Informe: `data/geo-h2-empirical-origin-revision-rate-2027-shadow.json`.

## Resultados de la reproducción oficial

Se han conservado los 199 países de entrenamiento y todos los país-años de categorías iniciales 0 y 1 hasta 2021. Las tasas se estimaron a partir de dos pares consecutivos y se evaluaron en el tercero, sin emplearlo para ajustar los pesos.

| Estado original | Exposiciones de entrenamiento | Reclasificaciones al estado contiguo | Tasa suavizada Jeffreys | Exposiciones reservadas 25.1→26.1 | Reclasificaciones reservadas | Frecuencia reservada |
|---|---:|---:|---:|---:|---:|---:|
| 0 → 1 | 10.083 | 6 | 0,0006445855 | 5.037 | 4 | 0,0007941235 |
| 1 → 0 | 611 | 0 | 0,0008169935 | 306 | 2 | 0,0065359477 |

La tasa estimada para 1→0 subestima la observada en el par reservado casi **ocho veces**; el resultado se basa en **solo dos eventos**, así que no demuestra estabilidad ni calibración fiable. Las observaciones históricas solapadas entre ediciones tampoco son independientes. **Ninguna de las tasas es una estimación validada de verdad latente**.

### Error histórico y nueva emisión experimental

| Origen histórico | Brier original | Brier mezcla editorial | Diferencia |
|---|---:|---:|---:|
| UCDP 23.1 | 0,044307424755 | 0,044309812569 | +0,000002387814 |
| UCDP 24.1 | 0,044259671874 | 0,044261995427 | +0,000002323554 |

El nuevo comparador **no mejora** el Brier histórico. La diferencia pequeña respecto al modelo duro es consistente con tasas de revisión inferiores al 0,1%, pero no autoriza a inferir mejor estabilidad prospectiva.

La nueva sombra independiente para objetivo **2027** contiene exactamente **196 probabilidades**, calculadas con UCDP 26.1 y corte 2025, y es una emisión distinta de la sombra anterior del 10%. Para GWNO 517 (Ruanda), la probabilidad del Markov duro es **0,239089456600**, y la de la mezcla por tasa editorial **0,239025443946**. Para GWNO 2 (Estados Unidos), respectivamente **0,045387672383** y **0,045541504889**.

[Informe SHA reproducible con las 196 nuevas probabilidades](../data/geo-h2-empirical-origin-revision-rate-2027-shadow.json) · [Reproductor](../scripts/experiment_geo_h2_empirical_revision_rate_shadow.py) · [Pruebas](../scripts/test_experiment_geo_h2_empirical_revision_rate_shadow.py).

### Conclusión y límites

Las revisiones editoriales son eventos raros en el universo completo de registros, pero **el dato del año inicial puede producir saltos individuales importantes** al cambiar de estado. Una frecuencia global de revisión baja no prueba que el estado registrado sea correcto; tampoco captura heterogeneidad por país, era o intensidad ni la revisión esperada después de una actualización de metodología UCDP. Se necesita un proceso de medición con estado latente o fuentes contemporáneas adicionales y validación prospectiva auténtica para justificar un nuevo estimador.
