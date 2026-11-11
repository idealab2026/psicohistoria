# GEO-2027 — Contraste exacto de alertas frente al azar condicionado por año

**11 de noviembre de 2026 · Experimento histórico exploratorio.** El resultado de 2027 no se ha observado y los vectores GEO-2027 y NEWCONF-2027 permanecen inalterados.

## Problema estadístico

La PR #50 comprobó que, entre **321 país-años inicialmente inactivos**, 10 alertas de entrada incluían 3 de las 8 entradas reales; y, entre **71 país-años inicialmente activos**, 5 alertas de resolución incluían 2 de las 10 resoluciones. Son números prometedores, pero aislados carecen de una referencia adecuada.

Además, las probabilidades, número de eventos y composición de la cohorte pueden cambiar entre **2024** y **2025**. Una evaluación combinada puede aparentar ordenar países cuando realmente está aprovechando diferencias entre años. Es necesario medir la discriminación dentro de cada año.

## Contraste fijado

Se conservan los dos conjuntos conocidos en el origen y sus cuatro subcohortes estado×año, sin cambiar ninguna predicción ni resultado: UCDP OrganizedViolenceCY **23.1 → 25.1** (2022→2024) y **24.1 → 26.1** (2023→2025), archivos SHA-256 verificables y previamente registrados.

Para cada una de las dos clases de alerta, y para capacidades fijas de **10 entradas** o **5 resoluciones**, se seleccionan las primeras probabilidades emitidas históricamente reconstruidas, **sin desempates arbitrarios**.

La referencia de azar es **exacta y condicionada por año**. Dados N países elegibles, K transiciones y k alertas seleccionadas en cada estado×año, el número de transiciones entre las alertas tiene distribución hipergeométrica:

\[
P(X=x)=\frac{\binom{K}{x}\binom{N-K}{k-x}}{\binom{N}{k}}.
\]

Las distribuciones anuales se convolucionan para el caso agrupado respetando cuántas alertas del top-k recaen en cada año. El informe publica la distribución completa de aciertos, el número esperado al azar, su rango central del 95 % y la probabilidad de obtener al menos los aciertos observados **si los resultados fueran intercambiables entre países del mismo año y estado inicial**.

Un empate en el corte de las alertas **anula la definición de una selección única** y, con ella, la inferencia de una cola precisa; se muestra explícitamente que el contraste no está definido. Así se evita adjudicar artificialmente aciertos mediante orden alfabético o un ID.

Adicionalmente, se calcula AUC con medio crédito para empates **dentro de cada año** y se promedian los AUC ponderando por pares positivo-negativo, excluyendo pares entre años que no aportan discriminación geográfica dentro de cada cohorte.

## Barreras de integridad

Se leen solo fuentes oficiales ya fijadas, se recompone la cohorte de 392 país-años (8 entradas, 10 resoluciones) y se exige que el informe anterior de alertas se reproduzca **en todos sus campos** antes de calcular este nuevo contraste. La salida contiene solo agregados, sin país, ID, etiqueta ni score individual. El contrato de CI ejecutará las pruebas sintéticas y recalculará el informe oficial, comparándolo byte a byte con el resultado archivado cuando sea publicado.

## Interpretación

El número de alertas y el modelo principal **ya se han evaluado sobre estos mismos resultados históricos**. Por tanto, cualquier probabilidad de cola hipergeométrica será **una referencia descriptiva condicionada, no un p-valor confirmatorio** ni una garantía de validez prospectiva. La hipótesis nula supone intercambiabilidad de etiquetas dentro de año×estado, que puede ser falsa por dependencia regional, conflictos compartidos y shocks simultáneos. No se han verificado por notaría independiente las fechas históricas de disponibilidad de todos los archivos.

La condición de éxito para hablar de capacidad predictiva real continúa siendo una evaluación futura no utilizada para diseñar ni ajustar el predictor. El contraste actual solo informa de si la concentración de alertas históricas es sorprendente bajo una referencia aleatoria explícita.

## Resultados de la edición archivada verificados en GitHub Actions

El informe original completo (incluidas las distribuciones nulas de todos los números de aciertos) está fijado en `data/geo2027-exact-alert-null-archival.json`. La auditoría reconstruye las 392 observaciones de UCDP y exige **igualdad byte a byte**.

| Magnitud | Entrada 0→1 | Resolución 1→0 |
|---|---:|---:|
| País-años | 321 | 71 |
| Cambios observados | 8 | 10 |
| Presupuesto de alertas agrupadas | 10 | 5 |
| Aciertos dentro de alertas | **3** | **2** |
| Aciertos esperados por azar, condicionado por año | **0.249709** | **0.766296** |
| P(azar iguala o supera aciertos), descriptiva | **0.00116470** | **0.163267** |
| Rango central nulo del 95 % de aciertos | **0–1** | **0–2** |
| AUC nacional dentro de año, ponderada por pares | **0.868211** | **0.766340** |
| AUC del Markov global dentro de año | **0.500000** | **0.500000** |

Distribución de las posiciones seleccionadas por origen temporal (presupuesto **agrupado**):

- Entradas: 6 alertas corresponden a 2024 (159 elegibles y 4 cambios) y 4 a 2025 (162 elegibles y 4 cambios). Aciertos observados: 3; el azar por grupos podría producir 3 o más con probabilidad **0.11647 %**.
- Resoluciones: 4 alertas corresponden a 2024 (37 elegibles y 6 cambios) y 1 a 2025 (34 elegibles y 4 cambios). Aciertos observados: 2; el azar por grupos podría producir 2 o más con probabilidad **16.32666 %**.
- El comparador Markov global tiene empates en las fronteras de las alertas, de modo que **no** se publica una probabilidad de cola arbitrariamente determinada mediante un desempate por ID.

La comparación mediante AUC dentro de año elimina la discriminación artificial obtenida solo de diferencias entre años. **El modelo nacional muestra mejor ordenación histórica que el Markov global, especialmente para entradas**, pero el valor 0.00116 **NO autoriza decir que la predicción de entradas está demostrada con p<0.05**: los resultados históricos ya habían sido inspeccionados, el predictor y las preguntas tienen historia de selección y los países no son completamente independientes. No se utiliza esta referencia condicionada para alterar el compromiso prospectivo GEO-2027.

**Decisión científica:** avanzar hacia una nueva cohorte de alertas prospectivas preregistrada independientemente, con utilidad económica o humanitaria definida y un conjunto de datos fuente-fechados, no seguir exprimiendo los mismos ocho cambios para construir un modelo cada vez más complejo.
