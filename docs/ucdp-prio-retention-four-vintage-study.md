# PSICOHISTORIA — Persistencia de conflicto intraestatal a dos años, cuatro cohortes separadas por edición

**12 de noviembre de 2026. Investigación EX POST, no predicciones emitidas entonces.**

## Pregunta y unidad de análisis

Entre los países que tenían al menos un conflicto **intraestatal UCDP/PRIO ACD** registrado en el año histórico de origen `t`, ¿cuáles presentan algún conflicto intraestatal de tipo 3 o 4 en `t+2`?

Es un problema de **persistencia de presencia de conflicto**: un país puede cambiar de conflicto y continuar clasificado como activo. Una etiqueta cero implica **ausencia de registros de conflicto intraestatal tipo 3/4 en la edición completa del año objetivo**, no declaración de paz, ausencia de violencia o menos de 25 muertos. Tampoco es onset2 ni la etiqueta GEO-2027 del UCDP Country-Year on Organized Violence. El conjunto de riesgo se forma exclusivamente con países que tenían conflictos registrados en el origen: no se añaden países nunca activos como supuestos negativos sin fuentes.

## Cuatro cohortes fijadas por fuente y fecha

| Fuente de origen disponible | Origen `t` | Fuente posterior del resultado | Objetivo `t+2` |
|---|---:|---|---:|
| UCDP/PRIO ACD 20.1 | 2019 | ACD 22.1 | **2021** |
| ACD 21.1 | 2020 | ACD 23.1 | **2022** |
| ACD 22.1 | 2021 | ACD 24.1 | **2023** |
| ACD 23.1 | 2022 | ACD 25.1 | **2024** |

Las fuentes 20.1, 21.1, 22.1, 23.1 y 25.1 ya tienen SHA-256 auditados en IDEA LAB. La edición **24.1**, necesaria para puntuar 2023 con su edición histórica correspondiente y no con la revisión 25.1, debe superar un procedimiento de certificación separado en esta PR: descarga oficial y revisión de formato, obtención de SHA-256, fijación en código, prueba de reproducción exacta y solo entonces evaluación. Las fechas de primera publicación no están notarizadas de forma independiente y estos pronósticos se **reconstruyen en 2026**, no se emitieron realmente en 2019–2022.

## Tres modelos de comparación definidos antes de puntuar

Todos utilizan exclusivamente registros de **la edición de origen**, con entrenamiento de pares `(año de origen histórico y, etiqueta objetivo y+2)` donde `y+2<=t`. El intervalo de entrenamiento empieza en 1990.

- **Tasa global reciente:** fracción histórica de países activos que permanecen activos dos años después, estimada en los últimos cinco años de origen elegibles hasta `t-2`. Suavizado Jeffreys de 0,5.
- **Historia país + shrinkage:** misma probabilidad de persistencia, utilizando los episodios previos del país y 12 pseudocuentas de la tasa global histórica; hiperparámetro fijado, sin ajuste sobre las cohortes posteriores.
- **Persistencia del año anterior:** tasa de persistencia histórica separada según si el país también estaba activo en el año inmediatamente anterior a cada origen histórico, suavizada con 12 pseudocuentas de la tasa global. Requiere observación de `t-1` solo en la fuente de origen.

Los modelos se comparan sobre los **mismos países y etiquetas de cada cohorte**. Se reportan Brier, log-loss, recuentos esperados, recuentos observados, diferencia de Brier por cohorte y suma ponderada de los cuatro conjuntos. No se presentan p-valores por países como si fueran observaciones independientes; los países se repiten, comparten shocks globales y los años objetivos se solapan en la misma región.

**El diseño es exploratorio después de haber observado otros resultados históricos.** La existencia de una edición antigua no convierte automáticamente una comparación retrospectiva en predicción prospectiva confirmatoria.

## Controles duros

- Descarga ZIP únicamente desde `ucdp.uu.se` de cada edición exacta, SHA-256 oficial congelado y campo de tipo 3/4 con `gwno_a = gwno_loc` y un solo Gobierno.
- Rechazo de registros de conflicto-año duplicados, fechas futuras dentro de fuentes de origen, años objetivos distintos de `t+2` y países cuyo código no aparece en ningún año de la edición objetivo. Esa ausencia de país no se convertirá en cero.
- Las etiquetas de resultado solamente se leen desde la **edición posterior** y nunca se introducen en el entrenamiento.
- El universo completo de 196 países de GEO no se utiliza para fabricar negativos de ACD.
- Se comprueba la inmutabilidad de GEO-2027 original, el shadow, las 15 alertas y NEWCONF-2027: el experimento no cambia ninguna de esas predicciones.
- El informe final se archivará como `data/ucdp-prio-2021-2024-retention-four-vintage.json` y se recomputará byte a byte desde las fuentes oficiales en GitHub Actions.

## Restricciones de inferencia

Este análisis puede aportar **cuatro cohortes históricas de persistencia de conflicto** verdaderamente separadas por fuentes originales y posteriores. No identifica necesariamente dependencia entre países, no estima violencia estatal por umbral de muertes y no prueba que las probabilidades GEO-2027 sean correctas. La pregunta es deliberadamente más modesta, pero tiene definición verificable y no mezcla entidades científicas incompatibles.

## Resultados oficiales reproducidos y fuente 24.1 fijada

Se ha incorporado **UCDP/PRIO ACD 24.1** con su ZIP institucional y SHA-256 inmutable `35c157c5f5aa2b08dc5b268bab7f0125da504ec3aa9dc5f28c9adba93b1717f5`. Así, el año objetivo 2023 se coteja con su edición 24.1, no con una revisión 25.1 disponible después.

La auditoría reconstruye ahora el informe `data/ucdp-prio-2021-2024-retention-four-vintage.json` con las seis ediciones UCDP/PRIO, compara los hashes y exige igualdad exacta de sus bytes.

| Origen y objetivo | Países de origen con conflicto intraestatal | Continúan con registro dos años después | Brier global 5 años | Brier historia país | Brier actividad previa |
|---|---:|---:|---:|---:|---:|
| 2019 → 2021 | 35 | 29 | 0,1425 | 0,1536 | **0,1294** |
| 2020 → 2022 | 36 | 29 | 0,1599 | 0,1629 | **0,1451** |
| 2021 → 2023 | 32 | 29 | **0,0893** | 0,1031 | 0,1014 |
| 2022 → 2024 | 34 | 29 | 0,1262 | **0,1203** | 0,1300 |
| **Ponderado por 137 evaluaciones** | **137** | **116** | 0,1306 | 0,1360 | **0,1271** |

Todos los modelos observan exactamente el mismo indicador ACD dentro de cada cohorte. La tasa global reciente de cada origen se estima exclusivamente con la fuente de origen, igual que el modelo de historia específica del país y la tasa condicionada a actividad en `t−1`.

El resultado **no respalda una superioridad consistente** del modelo de actividad anterior: gana en dos de los cuatro objetivos y su ventaja en Brier agregado sobre la tasa global es apenas **0,00347**. El Brier del modelo de historia país es peor que el de la tasa global agregada (0,1360 frente a 0,1306), aunque resulte ganador en el año 2024.

La tasa observada de persistencia es **116/137 = 84,67 %**, pero **no es una tasa mundial de persistencia de todos los conflictos**: el denominador son países-año seleccionados por presencia en origen, algunos países contribuyen en varios años y cada país puede albergar más de un conflicto. Un país que deja de aparecer en ACD puede haber dejado de tener conflictos del tipo analizado, sin implicar una declaración de paz o ausencia de otras violencias.

El estudio es retrospectivo, con diseño exploratorio y 4 años objetivo. Las fuentes están separadas por edición y congeladas por SHA-256, pero no hay evidencia de emisión auténtica de las probabilidades en 2019–2022 ni validación independiente de sus fechas de primera publicación. **No se estima correlación entre países**, no se publican p-valores IID y no se añade ningún resultado observado para 2027.

## Decisión

Mantener **la persistencia intraestatal ACD** como línea experimental diferenciada. No trasladar directamente sus métricas de Brier ni su tasa de continuidad al pronóstico GEO-2027, al shadow o a NEWCONF-2027. Solo se podrá estudiar su utilidad como variable origin-only en futuras hipótesis y con definiciones de país, fecha y endpoint compatibles.
