# GEO-2027 — Frontera exacta de victoria del modelo original frente al shadow

**12 de noviembre de 2026 · Diagnóstico previo a los resultados de 2027.**

Esta investigación no modifica las emisiones prospectivas ya publicadas. El objetivo es contestar una pregunta bien definida: **¿qué combinación de cambios de estado entre los 196 países hará que el Brier del modelo original sea mejor que el del shadow?** La respuesta matemática se obtiene a partir de los dos vectores de probabilidad originales, sin introducir nuevas fuentes ni datos de 2026/2027 y sin suponer independencia entre países.

La primera emisión del pronóstico GEO-2027 original es `3bb3561c8d6182c30624591276c705fb76ce99dc` y el segundo pronóstico shadow es `ed3e764a191b24bc2a01f4d877b115db2e247a20`. Las huellas SHA-256, el manifiesto y el generador de shadow se auditan **antes** de iniciar cualquier cálculo; cualquier alteración del vector emitido provoca fallo. Los resultados prospectivos de 2027 siguen en **cero**.

## Identidad algebraica sin modelo de dependencia

Para país `i`, sea `s_i` su estado conocido en **2025**: 1 si alcanza el umbral de 25 muertes de violencia organizada estatal, 0 en caso contrario. El pronóstico original da `p_i`, probabilidad de estado activo en 2027, y el *shadow* da `q_i`.

El cambio futuro de estado se expresa como `T_i = 1[Y_{i,2027} ≠ s_i]`.

La contribución del país a la **diferencia de Brier shadow − original** es

\[
\Delta_i=(q_i-Y_i)^2-(p_i-Y_i)^2
=\underbrace{(q_i-s_i)^2-(p_i-s_i)^2}_{b_i<0}
+T_i\underbrace{2|q_i-p_i|}_{w_i>0}.
\]

El shadow se construyó reduciendo la probabilidad de transición respecto al original, de manera estrictamente monótona dentro de cada conjunto de riesgo. Por eso `b_i<0` cuando el estado de 2027 persiste, y cada transición le impone una penalización positiva adicional `w_i`.

La comparación sobre los 196 países se reduce exactamente a

\[
\Delta Brier=\frac{1}{196}\left(\sum_i b_i+\sum_i T_i w_i\right).
\]

**Un resultado negativo favorece al shadow; uno positivo favorece al original.** No es un p-valor, una distribución de probabilidad ni un criterio modificado después de la emisión: es exactamente la diferencia de Brier definida en el contrato prospectivo de la PR #57.

## Cotas exactas condicionadas al número K de cambios

Si únicamente supiéramos que **exactamente K países cambian de estado**, pero todavía desconociéramos cuáles, los límites matemáticos más precisos de la diferencia de Brier son:

\[
\begin{aligned}
\min_{|S|=K}\Delta Brier &=\frac{\sum_i b_i + \sum_{j=1}^K w_{(j)}}{196},\\
\max_{|S|=K}\Delta Brier &=\frac{\sum_i b_i + \sum_{j=1}^K w_{[j]}}{196},
\end{aligned}
\]

donde `w_(j)` son las K penalizaciones **menores** y `w_[j]` las K **mayores**.

El resultado es **agudo (sharp)**: hay una asignación hipotética de exactamente K cambios que alcanza cada extremo. La clasificación para cada `K=0,...,196` es:

- **Shadow necesariamente mejor** si incluso el extremo máximo sigue siendo negativo.
- **Original necesariamente mejor** si incluso el mínimo es positivo.
- **Identidad de los países decisiva** si ambos signos siguen siendo factibles.

La misma operación se publica por separado para los 162 países inicialmente inactivos y los 34 activos. Cuando se conoce la distribución de `K` por ambos grupos, basta sumar las dos cotas condicionadas correspondientes y dividir por 196. No se escogen países a posteriori para declarar victoria, solo se establece de antemano el conjunto de resultados posibles.

Estos límites son matemáticos sobre todas las asignaciones binarias posibles; **no implican que todas esas combinaciones sean geopolíticamente realizables**. Tampoco asignan probabilidades a K ni a los países que cambian.

## Comprobación mediante puntuación estrictamente propia

Si, de manera puramente hipotética, las probabilidades **originales** describieran las verdaderas marginales de 2027, el valor esperado de la diferencia de Brier sería

\[
\mathbb E_{p}[\Delta Brier]
=\frac{1}{196}\sum_i(q_i-p_i)^2\geq 0.
\]

Si las marginales correctas fueran, en cambio, las del **shadow**, el mismo valor esperado sería exactamente el negativo:

\[
\mathbb E_{q}[\Delta Brier]
=-\frac{1}{196}\sum_i(q_i-p_i)^2\leq 0.
\]

Son identidades del carácter **estrictamente propio del Brier**, válidas sin independencia entre países. **No sabemos cuál de las dos familias de probabilidades, si alguna, describe el mundo real**. El análisis no decide el ganador antes de observar 2027.

## Reglas de publicación y reproducibilidad

`scripts/diagnose_geo2027_shadow_break_even.py` obtiene el conjunto de 196 probabilidades de ambas emisiones públicamente verificadas. Genera el vector completo de cotas por número de transiciones, las fronteras por estado inicial, la clasificación determinista de cada caso y los diez países con **mayor influencia matemática sobre la diferencia de pérdidas**. Estos últimos **no son los diez países de mayor riesgo de transición**, y la diferencia importa.

Una auditoría GitHub Actions ejecuta pruebas con conjuntos **sintéticos** que enumeran exhaustivamente todas las combinaciones de tres países, además de contrastar límites para cambios escogidos entre los 196 originales frente al evaluador emparejado de la PR #57. El informe congelado debe reproducirse **byte a byte** desde los dos compromisos de emisión. Ningún 2027 simulado se registra como si fuera un resultado oficial.

El futuro resultado real exigirá la cobertura oficial completa de los 196 países y seguirá distinguiendo métricas originales frente a secundarias, incertidumbre geopolítica y selección históricamente exploratoria del método shadow.
