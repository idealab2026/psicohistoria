# GEO H2 · Ruanda 1996 frente a 2021: descomposición exacta de revisiones

**Diseño retrospectivo · 18 de noviembre de 2026.** Se descompone la subida de probabilidad histórica de violencia estatal Ruanda (GWNO 517) para el objetivo 2023 de 0,159390196535 (fuente de origen 23.1) a 0,272686169101 (24.1).

El modelo de cuatro estados utiliza solo categorías **0, 1–24, 25–99, ≥100** muertes, con horizonte dos años, prior Dirichlet de uno y shrinkage de 20. Se mantienen el mismo estimador, origen simulado 2021 y los 199 países de entrenamiento que contenían las fuentes oficiales. Solo 196 pertenecen a la cohorte de evaluación.

## Intervenciones predefinidas

Se tratan como factores distintos las cuatro modificaciones oficiales de Ruanda: 1996 (90→113), 1997 (980→985), 2018 (6→9) y 2021 (0→7). Un quinto factor sustituye todas las revisiones de los restantes 198 países de entrenamiento. En total se calculan las **32 combinaciones posibles**, sobre los archivos UCDP 23.1 y 24.1 con SHA-256 verificado.

Para cada factor se promedian exactamente todas las permutaciones de intervención (Shapley de cinco factores). Las cinco contribuciones deben sumar el cambio original de **+0,113295972566** de probabilidad.

Los dos cambios de recuentos **1997 y 2018 no cruzan los umbrales de intensidad**: este modelo categórico tiene que producir exactamente la misma salida al cambiar solo esos registros, cualquiera que sea el resto de las intervenciones. La auditoría rechaza una desviación incluso si es pequeña.

**Objetivo de inferencia:** separar el cambio que afecta al estado inicial de 2021 de la revisión de transición antigua de 1996, manteniendo explícita cualquier interacción y el efecto de los restantes 198 países. La suma de Shapley por subfactores no tiene por qué ser idéntica a un Shapley en el que esos factores se agrupan primero; son juegos de intervención diferentes con interacciones.

## Condiciones de publicación

Se reproducen los cuatro resultados extremos del experimento de dos bloques ya publicado en la PR #121 y las dos probabilidades previamente conservadas. No se publican cifras de contribuciones individuales hasta que GitHub Actions verifique el replay. La auditoría también comprueba la integridad de GEO2027 y la cohorte institucional.

Este experimento usa ediciones publicadas después del pseudo-origen 2021; no acredita habilidad predictiva prospectiva ni atribuye causalidad sobre el conflicto histórico. Las predicciones y alertas futuras no se modifican.
