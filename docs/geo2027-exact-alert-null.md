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
