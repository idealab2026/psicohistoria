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

## Resultados verificables: influencia local frente a prior global

El informe fuente-auditado reconstruye las **143 comparaciones por país** ya utilizadas en la prueba del calibrador LOG1P excluyente, distribuidas en **13 bloques año–edición** y nueve años objetivos distintos. Las siete pruebas matemáticas pasan, y el escenario Markov original reproduce exactamente el offset original de H2 y el Brier ya publicado en el estudio precedente.

En la versión UCDP **26.1**, la diferencia de Brier **α1−α0** (signo negativo favorece conservar LOG1P continuo) queda así:

| Año | GEO original con historia local | Excluir del prior global, conservar la historia local | Excluir también las transiciones locales | Cambio de signo |
|---|---:|---:|---:|---|
| **2017** | +0,000121285 | +0,000119929 | **−0,000052598** | **Sí** |
| 2018 | −0,001040765 | −0,001041119 | −0,000610676 | No |
| 2019 | −0,001055160 | −0,001056395 | −0,000868172 | No |
| 2020 | −0,001918235 | −0,001916797 | −0,000964031 | No |
| 2021 | −0,000237424 | −0,000240199 | −0,000715833 | No |
| 2022 | −0,000282796 | −0,000286319 | −0,000749138 | No |
| 2023 | −0,000610833 | −0,000617021 | −0,000910361 | No |
| **2024** | −0,000821282 | −0,000825549 | **−0,001144147** | No |
| **2025** | +0,000634712 | +0,000632571 | **+0,000092863** | No |

La señal LOG1P no se elimina en estos escenarios; la intervención recae exclusivamente sobre el Markov. Los resultados se refieren a **pérdida Brier emparejada de las dos variantes**, no a una nueva emisión. Al quitar las transiciones propias del prior global pero mantener las locales, las diferencias son minúsculas: en los países subumbrales, el desplazamiento Markov absoluto medio es **0,0216 pp (2017)**, **0,0205 pp (2024)** y **0,0154 pp (2025)**. Por tanto, la influencia de esos países sobre el prior global no explica la variación importante.

En cambio, **su historial local sí importa**: respecto al prior global sin el país, conservar las transiciones locales desplaza las probabilidades Markov una media de **4,78 pp en 2017**, **6,89 pp en 2024** y **4,40 pp en 2025**. Los desplazamientos absolutos máximos de los tres años son **18,04 pp**, **21,35 pp** y **13,19 pp**. Estos valores son diferencias de probabilidades Markov, no Brier ni errores de estimación.

### 2017: cambia la conclusión al suprimir el historial local

**Israel** es el principal contribuyente a la inversión de signo. En el origen 2015 registra **10 muertes** (por debajo del umbral 25) y el resultado estatal de 2017 queda por debajo de 25. Su Markov original reconstruido estima **23,75 %**, pero el contrafactual de prior global sin transición local (con estado 2015 aún conocido) estima **5,62 %**. Con los mismos coeficientes LOG1P entrenados sin sus etiquetas, la probabilidad α=1 pasa de **31,84 %** a **8,20 %**. Esto cambia considerablemente la penalización Brier por elevar el riesgo.

El signo del contraste de 2017 pasa de **+0,000121** a **−0,000053** al retirar toda historia local. El resultado aparece también en las cuatro ediciones oficiales 23.1, 24.1, 25.1 y 26.1. No equivale a una demostración de que un modelo global-only reentrenado hubiese acertado mejor: se preservan los coeficientes logísticos anteriores y se impone un offset distinto.

### 2024 y 2025: efectos heterogéneos pero sin inversión

En **2024**, la ventaja Brier de α1 aumenta con el offset global-only, pero la aportación de **Angola** se reduce notablemente: su Markov H2 pasa de **23,86 %** a **5,43 %**, y su LOG1P α1 de **42,33 %** a **11,86 %**; como sí cruza el umbral en el resultado, el decremento de esa probabilidad puede ser perjudicial individualmente. Sin embargo, también se reducen riesgos excesivos para países que no se activaron, como **Burundi**, cuyo Markov pasa de **26,80 %** a **5,40 %** y α1 de **39,37 %** a **9,19 %**. **El balance neto favorece aún más a α1, pero no todos los países mejoran.**

En **2025**, la desventaja de α1 se reduce de **+0,000635** a **+0,000093**; una disminución relativa aproximada de **85,4 %** del perjuicio Brier. Destaca **Uganda**, que pasa de Markov H2 **13,14 %** y α1 **25,93 %** a **5,41 %** y **11,69 %** en el escenario global-only. Tampoco se invierte el signo, por lo que sigue sin justificarse declarar superioridad universal de la intensidad LOG1P.

### Alcance científico

- En el conjunto de **13 bloques**, solo **las cuatro versiones de 2017** invierten signo; en los nueve años únicos, solo **2017**.
- El efecto de quitar el país **solo del prior global** es muy pequeño. Su historia **local** tiene una influencia grande en varios casos, que puede resultar beneficiosa o perjudicial para el Brier según el resultado.
- En el escenario global-only se conoce el estado actual del país, pero se **desajusta potencialmente la distribución de offsets** frente a la usada para entrenar la logística. **No es un modelo alternativo de producción ni una validación prospectiva de cold-start.**
- No se emite ni optimiza ningún algoritmo con estas comparaciones históricas, y 2027 sigue sin resultados oficiales resueltos.

## Cobertura y auditoría

Se replican los **13 bloques año-edición de la prueba previa**, con nueve años distintos (2017–2025) en UCDP 26.1, además de 2017 en las ediciones 23.1,24.1,25.1 y 2024 en 25.1. Cada país elegible se selecciona solo porque tiene **1–24 muertes en el año de origen**; no se selecciona basándose en su resultado futuro.

Por bloque se reporta el Brier emparejado α1−α0 para los tres escenarios, siempre con el mismo denominador de países observables del año (los países cuyo origen es 0 o ≥25 tienen diferencia α1−α0 nula *bajo el mismo offset y el mismo β*). Se reportan además las pérdidas dentro del grupo subumbral para ambos modelos, cambios de signo al retirar el historial, amplitud media/máxima de perturbación de probabilidad Markov en puntos porcentuales, y los países más influyentes.

Se verifica en el baseline la **igualdad exacta de cada probabilidad Markov H2 con el cálculo original** y la igualdad del ΔBrier previo de calibración por país. Si el Markov local o la resta de conteos del global están mal implementados, la reproducción **falla**. Los 196 pronósticos GEO originales, las 196 probabilidades de la sombra LOG1P y las 15 alertas están blindadas por sus SHA ya publicados. **Cero resultados oficiales 2027**.

**Sin nueva emisión:** no se elige una variante nueva ni se modifica ningún archivo de pronóstico. Este es un informe de investigación retrospectiva y no un resultado de capacidad predictiva prospectiva demostrada.

Archivos: \`scripts/experiment_geo2027_log1p_markov_country_history_ablation.py\`, \`scripts/test_experiment_geo2027_log1p_markov_country_history_ablation.py\`, \`data/geo2027-log1p-markov-country-history-ablation.json\`. GitHub Actions verifica las cuatro ediciones oficiales por SHA y exige igualdad de bytes del informe antes de la publicación.
