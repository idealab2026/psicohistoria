# ACD · Influencia histórica por país y parejas (2021–2024)

**13 de noviembre de 2026.** Análisis ex post de sensibilidad, **no** una prueba prospectiva independiente. GEO2027, NEWCONF2027 y ACD2027 originales permanecen inmutables, con **0 resultados de 2027** observados.

## Pregunta científica

¿La ligera ventaja histórica del modelo ACD p_lag1_group frente a la referencia global p_global_recent5 depende de ciertos países? Comparamos también p_country_eb con la misma referencia, sin seleccionar un nuevo modelo primario.

Se reconstruyen desde **seis ediciones UCDP/PRIO ACD con SHA-256 fijado** cuatro parejas origen→objetivo: **2019→2021, 2020→2022, 2021→2023 y 2022→2024**, con ediciones de origen y objetivo separadas. Solo entran países con conflicto intraestatal tipo 3/4 registrado en el año de origen, nunca un universo inventado de países inactivos. La ausencia de registro ACD en el objetivo **no significa paz**.

El script reproduce primero el informe publicado de cuatro cohortes y sus pérdidas Brier. La muestra histórica contiene **137 puntuaciones país-año, 116 desenlaces con presencia de conflicto, 42 códigos GWNO únicos**; 37 aparecen en más de un año. Distribución: 5 países con una evaluación, 5 con dos, 6 con tres y 26 con cuatro. Estos 137 casos **no son independientes**.

## Método: eliminación fija, no reentrenamiento

Sea \(d_{it}=(p_{it,\mathrm{candidato}}-y_{it})^2-(p_{it,\mathrm{global}}-y_{it})^2\). La diferencia global publicada es:

\[
\bar d = \frac{\sum_{it}d_{it}}{137}.
\]

Para excluir un conjunto de países \(S\), se retiran **todas** sus evaluaciones históricas, dejando **intactas** las probabilidades, los hiperparámetros y el resto de observaciones:

\[
\bar d_{-S} =
\frac{\sum_{it:\,i\notin S}d_{it}}
{137-\#\{(i,t):i\in S\}}.
\]

Se calculan exhaustivamente las **42 exclusiones individuales** y las **861 parejas no ordenadas** (42 × 41 / 2), para ambos modelos candidatos. Signo negativo: el candidato obtuvo menor Brier que la referencia global; positivo: ganó la referencia. No es cross-validation, no estima la pérdida tras reentrenamiento y no crea observaciones nuevas.

## Resultados reconstruidos

| Comparación candidato − global | Brier inicial | Rango al excluir un país | Inversiones (un país) | Inversiones (dos países) |
|---|---:|---:|---:|---:|
| lag1_group − global_recent5 | **−0,0034723490** | −0,0052137932 a −0,0001193487 | 0/42 | **27/861** |
| country_eb − global_recent5 | **+0,0053866397** | +0,0031148632 a +0,0081824944 | 0/42 | **0/861** |

Ninguna exclusión individual invierte el signo. Sin embargo, la ventaja de lag1 casi desaparece al eliminar **Tanzania** o **Argelia**, por separado: Δ Brier = **−0,0001193487** en ambos casos. Son países con una única puntuación histórica en la cohorte, y cada puntuación tiene la misma diferencia de pérdidas (−0,4594804), favorable a lag1.

Excluyéndolos **simultáneamente**, la diferencia se invierte a **+0,0032833258** sobre los 135 registros restantes: el **global** supera a lag1. También ocurre con **Estados Unidos + Tanzania**, o **Estados Unidos + Argelia** (ambas +0,0031814182). En total, **27 de las 861 parejas** provocan reversión. Para country_eb, ni siquiera dos exclusiones invierten su resultado desfavorable respecto al global.

**No interpretar 27/861 como p-valor, probabilidad de reversión o frecuencia de un experimento aleatorio.** Son combinaciones matemáticamente enumeradas sobre la misma muestra observada y los mismos modelos, tras haber inspeccionado resultados históricos.

## Interpretación y límites

El modelo lag1 superó descriptivamente al global en la muestra original, pero la clasificación es **sensible a retirar dos países**. Esto debilita la afirmación de superioridad general y la extrapolación a 2027, aunque no permite predecir el ganador futuro.

Los conjuntos de riesgo cambian entre años; países y shocks geopolíticos se repiten. Las ediciones fuente archivadas están verificadas por hash, pero los pronósticos históricos no fueron publicados de forma independiente en sus fechas de origen. El análisis permanece **exploratorio**, no confirmatorio. El modelo ACD2027 primario sigue siendo p_global_recent5, y sus secundarios conservan la misma condición exploratoria que en su primera emisión.

## Trazabilidad

- Reproducibilidad: scripts/diagnose_acd_retention_country_influence.py --summary --check-report data/acd-historical-country-influence.json.
- Informe derivado verificable: data/acd-historical-country-influence.json. Contiene recuentos de inversiones, extremos y principales contribuciones, pero no etiquetas de 2027.
- Pruebas: scripts/test_diagnose_acd_retention_country_influence.py, con casos sintéticos de países repetidos, pérdidas emparejadas, eliminaciones individuales y de dos países, entradas inválidas y ausencia de reentrenamiento.
- Workflow institucional: pruebas y reconstrucción completa de fuentes históricas en un job obligatorio de verificación, incluido en la cadena de despliegue. Las tres cohortes de pronóstico prospectivo conservan sus hashes de primera publicación.

**Siguiente cuestión investigable:** si el resultado cambia bajo bloques temporales suficientemente distantes y distintas familias de variables, sin elegir modelos basándose en los años usados como prueba. La sensibilidad por país no identifica shocks comunes ni establece skill independiente.
