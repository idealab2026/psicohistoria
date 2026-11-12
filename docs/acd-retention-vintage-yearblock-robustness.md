# PSICOHISTORIA — Sensibilidad de la persistencia ACD a revisiones de edición y exclusión de años

**12 de noviembre de 2026. Estudio retrospectivo de robustez, no predicción emitida.**

## Pregunta

La línea ACD de la PR #62 reconstruyó cuatro evaluaciones con orígenes 2019–2022 y años objetivo 2021–2024, 137 evaluaciones de país-año y 116 persistencias registradas. La Brier agregada del modelo basado en actividad del año anterior (0,12713) fue ligeramente mejor que la tasa global reciente (0,13060).

Esta diferencia de **−0,00347** es pequeña y no es una prueba estadística confirmatoria. Este diagnóstico se propone medir su fragilidad frente a:

1. **Etiquetas retrospectivas revisadas:** manteniendo idénticas las probabilidades calculadas con la edición histórica de origen, reevaluar el mismo año objetivo en ediciones UCDP/PRIO ACD **posteriores**. El objetivo no se vuelve a entrenar.
2. **Bloques de calendario:** repetir el promedio de Brier tras **excluir uno de los cuatro años objetivo completos**. No se vuelve a entrenar ni se seleccionan hiperparámetros. Esta exclusión es una sensibilidad determinista, **no validación cruzada independiente**.

Las ediciones oficiales son las 20.1 (hasta 2019), 21.1 (2020), 22.1 (2021), 23.1 (2022), 24.1 (2023) y 25.1 (2024), cuyos ZIP oficiales y SHA-256 están fijados desde las PR #61 y #62.

## Revisión de etiquetas históricas sin contaminación temporal

Se mantiene el mismo país y año de origen, el mismo conjunto de riesgo con conflicto intraestatal tipo 3/4 registrado en ese año, y los mismos modelos estimados **con datos objetivo hasta el año de origen**.

| Objetivo | Edición original del resultado | Ediciones posteriores para sensibilidad |
|---|---|---|
| 2021 | 22.1 | 23.1, 24.1 y 25.1 |
| 2022 | 23.1 | 24.1 y 25.1 |
| 2023 | 24.1 | 25.1 |
| 2024 | 25.1 | Ninguna disponible en la serie fijada |

Se contabilizan los países activos en origen cuya etiqueta del **mismo año objetivo** pasa de 0→1 o de 1→0 entre ediciones, además del impacto en Brier de los tres modelos. Si un país del conjunto de riesgo deja de tener un código histórico reconocible en la edición posterior, se bloquea la comparación en lugar de inventar un cero.

La comparación agregada secundaria utiliza el objetivo 2021–2023 de la **última edición 25.1** y el objetivo 2024 de su única edición disponible 25.1. Se denomina explícitamente `latest_later_target_vintage_pooled_descriptive_only`: **no sustituye** los resultados originales de primera edición ni convierte la evaluación de origen en una emisión histórica real.

## Prueba de exclusión de un año completo

Para cada año `t∈{2021,2022,2023,2024}` se calcula la diferencia exacta de Brier del modelo actividad-previa menos global-reciente sobre los otros tres años:

\[
\Delta Brier_{-t}
=\frac{\sum_{y\ne t} n_y(\mathrm{Brier}_{actividad\ previa,y}-
\mathrm{Brier}_{global,y})}{\sum_{y\ne t} n_y}.
\]

Se hace tanto con las cuatro ediciones de resultado originales como con el corte final de revisión 25.1. **No** es una prueba de independencia temporal: los países se repiten, las fechas de horizonte se solapan y cuatro años son insuficientes para estimar varianzas geopolíticas. La utilidad es detectar **si la ventaja cambia de signo al excluir un año completo**, y si los cambios de edición alteran el ranking de modelos.

## Integridad y alcance científico

`scripts/diagnose_acd_retention_vintage_yearblock.py` recalcula primero el informe de cuatro cohortes **exactamente** desde los ZIP oficiales y exige coincidencia de todos sus campos con el JSON publicado de la PR #62, incluidos los 137 ejemplos y 116 positivos. Solo después aplica cambios de edición de la etiqueta objetivo. El código coteja que las tres **sumas de probabilidades esperadas por cohorte permanezcan idénticas** en todas las ediciones: cualquier variación implicaría un cambio encubierto de entrenamiento y fallaría.

La CI debe comparar el informe final `data/ucdp-prio-retention-vintage-yearblock-robustness.json` **byte a byte** contra su reconstrucción desde las seis ediciones. Los tests incluyen exclusión de años con ponderación correcta, cruces inválidos de ediciones, alteración de resultados y comprobación de que GEO-2027 original, shadow y alertas siguen intactos.

**No es GEO-2027:** el objetivo ACD es persistencia de cualquier conflicto intraestatal tipo 3/4 registrado dos años después entre países que tenían conflictos en el origen. No es un umbral de 25 muertes de violencia estatal, inicio de una guerra, cese de violencia ni paz negociada. No se crean nuevas predicciones 2027, no se introducen datos futuros y las fechas originales de edición no están independientemente notarizadas.

Los resultados son **exploratorios**, pues la hipótesis y los modelos se han propuesto después de explorar resultados históricos. Una variación de signo o la estabilidad de la ventaja entre tres años restantes deben interpretarse como una comprobación limitada de robustez, **nunca** como prueba de capacidad predictiva general.
