# GEO H2 · Influencia de cada país en la inversión del ranking de 2023

**Experimento retrospectivo (18/11/2026).** La PR #119 registró una inversión muy estrecha del orden relativo del modelo Markov binario y el Markov de cuatro estados, al cambiar únicamente la edición UCDP utilizada para reconstruir el origen histórico 2021.

## Pregunta

¿Qué países aportan a la diferencia observada cuando la misma etiqueta 2023 de UCDP OrganizedViolenceCY **26.1** se evalúa con probabilidades reconstruidas desde los orígenes **23.1 y 24.1**?

Para cada uno de los **196 GWNO oficiales congelados**, sea `y_i` la etiqueta fija de 26.1; `p4_i(v)` y `pB_i(v)` las probabilidades reconstruidas desde origen edición `v`.

```
margin_i(v) = (p4_i(v)-y_i)^2 - (pB_i(v)-y_i)^2
change_i = margin_i(24.1) - margin_i(23.1)
global_shift = sum(change_i) / 196
```

Se verifica que los márgenes globales reconstruidos para ambas ediciones son **exactamente** los conservados en la PR #119; la identidad, origen 2021 y objetivo 2023 no pueden cambiar y no se permiten ceros imputados por ausencia de una observación en la fuente.

El resultado incluye la tabla de los 196 países con probabilidades y contribuciones, los veinte mayores cambios absolutos y un análisis *leave-one-country-out* de sensibilidad de la inversión del ranking. **Este último elimina la contribución del país del cálculo del score, pero NO reentrena**: no es una estimación causal de su influencia sobre parámetros globales.

## Límites de identificabilidad

- UCDP 23.1 y 24.1 se publicaron después de 2021; estas probabilidades son reconstrucciones *ex post*, no emisiones históricas originales.
- La revisión de la fuente puede afectar a probabilidades globales de muchos países; el aporte de un GWNO a la **diferencia observada de Brier** no es necesariamente la causa de la revisión de esas probabilidades.
- El modelo no se reajusta ni se selecciona a partir del resultado 2023; las emisiones prospectivas de 2027/2028 no se modifican.
- No se presume independencia estadística entre países ni se atribuye significación a una diferencia de Brier muy pequeña.

## Resultados originales reconstruidos y fijados

La reproducción de los cuatro archivos oficiales UCDP por SHA, el origen 2021 y las 196 etiquetas idénticas de 2023 reproduce la inversión exacta registrada en la PR #119:

| Margen Brier: 4 estados menos binario | Origen 23.1 | Origen 24.1 |
|---|---:|---:|
| Objetivo 2023 fijo (UCDP 26.1) | −0,0002771979 | +0,0000349581 |

El cambio de margen es **+0,00031215598**. Se descompone exactamente como la suma de 196 contribuciones dividida entre 196. Los cinco mayores movimientos absolutos son:

| País (GWNO) | Cambio de contribución individual no normalizado |
|---|---:|
| Ruanda (517) | +0,04891129 |
| Uganda (800) | +0,01546486 |
| Kirguistán (703) | −0,00537892 |
| Mali (432) | −0,00513975 |
| Sudán (625) | +0,00467551 |

Las variaciones positivas desplazan la comparación hacia el binario, mientras que las negativas favorecen al modelo de cuatro estados. Ruanda y Uganda suman aportes positivos superiores al movimiento neto porque existen aportes compensatorios.

**Análisis de influencia:** al retirar una sola contribución país-año (sin reentrenar) se pierde la inversión del ranking en **29 de las 196** exclusiones posibles. Por tanto, no sería válido afirmar que el cambio de ganador está explicado por un único país causal: los márgenes son suficientemente pequeños para que muchos países resulten decisivos *en un leave-one-out de evaluación*.

[Informe JSON completo con 196 países y 196 experimentos leave-one-out](../data/geo-h2-2023-country-origin-vintage-rank-influence.json).

El informe y las probabilidades originales se reproducen desde las fuentes oficiales y son comprobados por igualdad exacta de datos en CI. Las fechas de origen siguen siendo simuladas retrospectivamente.
