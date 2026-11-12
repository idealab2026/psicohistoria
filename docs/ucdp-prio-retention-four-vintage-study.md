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
