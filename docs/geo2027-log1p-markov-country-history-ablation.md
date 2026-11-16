# GEO2027 LOG1P — Dependencia del historial nacional en el Markov

**Protocolo de ablación de fuente histórica y transferibilidad · 16/11/2026.** Continúa la investigación de transferencia del calibrador continuo de intensidad 1–24 muertes, ya ejecutada en 13 bloques año–edición y 143 casos con todas las etiquetas de entrenamiento del país excluidas del calibrador. **No se actualizan emisiones de 2027.**

## Pregunta concreta

La exclusión de las etiquetas históricas de un país en el ajuste logístico mantuvo la dirección de la mejora del Brier en nueve años. Pero la probabilidad de referencia GEO H2 proviene de un Markov con dos componentes:

1. Un prior de transición común, construido acumulando las transiciones históricas de todos los países (incluido el que se está evaluando).
2. Transiciones particulares del país evaluado, combinadas con el prior común con la regularización de veinte transiciones.

Así, la prueba anterior de calibración excluyente **todavía permitía que el país influyese en los parámetros del Markov**. Este estudio cuantifica esa influencia, separando dos niveles y **manteniendo los parámetros de calibración logísticos constantes** para evitar atribuirles cambios que procedan de una recalibración.

## Tres escenarios algebraicos de Markov H2

Para el objetivo histórico \`t\`, se fija el origen \`o=t−2\`. Se contabilizan exclusivamente las transiciones anuales de la fuente oficial UCDP **hasta o**, nunca después. El modelo de referencia tiene \(q_s=(n_{s\to1}^{c}+20g_s)/(n_s^c+20)\), donde \(n^c\) son los conteos de transición del país, y \(g_s=(N_{s\to1}+1)/(N_s+2)\) es el prior global Laplace-1. La probabilidad a dos pasos es \((1-q_{s_o})q_0+q_{s_o}q_1\).

Los tres escenarios quedan fijados antes de comparar resultados:

- **Original con historia nacional y contribución al global:** la misma probabilidad Markov H2 del estudio anterior. Se exige igualdad exacta hasta 12 decimales con su cálculo histórico original.
- **Excluir al país del prior global, conservar su historia local:** se restan *todas* sus transiciones de \(N_s\) y \(N_{s\to1}\) del global, se recalcula \(g_s^{-c}\) y se mantiene su \(n^c\) dentro del shrinkage de 20 transiciones. Así se aísla cuánto contaminaba la estimación del prior común consigo mismo.
- **Excluir al país del global y también de los conteos de transición locales:** el pronóstico Markov usa exclusivamente \(g_s^{-c}\) (sin \(n^c\)) y el **estado binario observado en el año de origen**. Se trata de una predicción de un país que aporta únicamente su estado presente, **no de un país enteramente desconocido**.

A lo largo de esos tres escenarios se emplea para cada país **exactamente el mismo vector β logístico reajustado sin ninguna de sus etiquetas históricas** (ridge λ=5), obtenido con la metodología de la investigación anterior. Las probabilidades α=0 y α=1 se evalúan sobre esos tres offsets Markov alternativos.

## Precisión metodológica decisiva

Esta prueba no es un pipeline completo de Markov global-only más calibrador reentrenado específicamente para ese tipo de offset: **el calibrador se aprendió con offsets Markov que incluían información local de los países que sí estaban en su entrenamiento**. Aplicarlo al tercer escenario sin reajustarlo crea una posible *covariate shift* de offsets. Por eso el tercer resultado mide sensibilidad mecanística del pronóstico al historial nacional y su interacción con LOG1P, **no acredita un modelo cold-start calibrado para nuevos países**.

El resto de las salvaguardas permanece fijo: la familia α=0/1 y λ=5 se definieron después de estudiar históricos; el ajuste de la logística termina en \`t−2\`, las variables de sus filas históricas como máximo en \`t−4\`, y las tres probabilidades Markov del país solo ven información hasta \`t−2\`. Las ediciones UCDP se publicaron después de varios años evaluados y pueden haber revisado retroactivamente los historiales. **Ningún país o año de edición se trata como observación independiente IID**.

## Cobertura y auditoría

Se replican los **13 bloques año-edición de la prueba previa**, con nueve años distintos (2017–2025) en UCDP 26.1, además de 2017 en las ediciones 23.1,24.1,25.1 y 2024 en 25.1. Cada país elegible se selecciona solo porque tiene **1–24 muertes en el año de origen**; no se selecciona basándose en su resultado futuro.

Por bloque se reporta el Brier emparejado α1−α0 para los tres escenarios, siempre con el mismo denominador de países observables del año (los países cuyo origen es 0 o ≥25 tienen diferencia α1−α0 nula *bajo el mismo offset y el mismo β*). Se reportan además las pérdidas dentro del grupo subumbral para ambos modelos, cambios de signo al retirar el historial, amplitud media/máxima de perturbación de probabilidad Markov en puntos porcentuales, y los países más influyentes.

Se verifica en el baseline la **igualdad exacta de cada probabilidad Markov H2 con el cálculo original** y la igualdad del ΔBrier previo de calibración por país. Si el Markov local o la resta de conteos del global están mal implementados, la reproducción **falla**. Los 196 pronósticos GEO originales, las 196 probabilidades de la sombra LOG1P y las 15 alertas están blindadas por sus SHA ya publicados. **Cero resultados oficiales 2027**.

**Sin nueva emisión:** no se elige una variante nueva ni se modifica ningún archivo de pronóstico. Este es un informe de investigación retrospectiva y no un resultado de capacidad predictiva prospectiva demostrada.

Archivos: \`scripts/experiment_geo2027_log1p_markov_country_history_ablation.py\`, \`scripts/test_experiment_geo2027_log1p_markov_country_history_ablation.py\`, \`data/geo2027-log1p-markov-country-history-ablation.json\`. GitHub Actions verifica las cuatro ediciones oficiales por SHA y exige igualdad de bytes del informe antes de la publicación.
