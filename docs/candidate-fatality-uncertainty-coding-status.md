# PSICOHISTORIA · UCDP Candidate: sensibilidad `low/best/high` y `code_status` (protocolo 20-11-2026)

**Prerregistro de auditoría de incertidumbre antes de ejecutar este nuevo cálculo.** Estudio de sensibilidad **posterior a observar** el resultado favorable de Kenia y Libia. No es una predicción nueva ni validación independiente del modelo.

## Pregunta

El experimento anterior obtuvo dos casos de reactivación de ≥5 muertes de violencia estatal registradas del **1 al 30 de mayo de 2026** (Kenia y Libia), partiendo de <5 muertes de esa categoría entre enero y marzo. El mismo umbral sobrevivió al cambio de Candidate Q2 a Q3; ahora determinar:

1. ¿Cuántos países superan el umbral bajo las sumas **`low`, `best` y `high`** de UCDP, con el **mismo conjunto de eventos**? `low` y `high` son estimaciones descriptivas de incertidumbre, **no intervalos de confianza probabilísticos**.
2. ¿Qué parte del resultado `best` depende de eventos señalados por `code_status`? Publicar una sensibilidad adicional que conserva solo eventos cuyo `code_status`, normalizado por espacios y mayúsculas, sea **`Clear`**. No llamar al resto incorrecto ni a `Clear` un certificado de inclusión GED anual.
3. ¿Se mantienen las etiquetas de mayo en las ediciones Q2 (enero–junio) y Q3 (enero–septiembre) de los mismos años 2024–2026? Además evaluar solo en **Q3** el horizonte de 90 días (1 mayo–29 julio de 2026).
4. ¿Qué cambia para las diez alertas 2026 mejor puntuadas del modelo **combinado ya congelado**, si se usan estas variantes de etiqueta? Calcular para `low/best/high/clear_best` aciertos top10 corregidos por empates; **no ajustar ni volver a estimar probabilidades**.

## Origen y controles fijados

- Exactamente **nueve** originales UCDP Candidate Q1, Q2 y Q3, 2024–2026. URL y SHA-256 deben coincidir con el registro congelado `data/candidate-may-threshold-vintage-stability.json`. No utilizar CSV anual ni otros años. Cada descarga fallará si cambia un solo byte.
- Universo 196 países, idéntico al registro GEO2027. Fuente y SHA del universo ya están congelados en el experimento `data/candidate-reactivation-threshold-grid.json`.
- **Conjunto de riesgo, invariable:** países con menos de **5 `best`** de violencia estatal en Q1. No reconstruir el conjunto de riesgo con `low` o `high` (eso cambiaría la población a posteriori).
- Eventos de origen y resultados únicamente `type_of_violence=1`, `date_prec∈{1,2}`, con intervalo `[date_start,date_end]` **completo dentro de la ventana** y `country_id` del universo. Quedan excluidos `date_prec=0`, fechas ambiguas, eventos cruzando fronteras y violencia de tipo 2/3 para el objetivo. No atribuir muertes de eventos multidiarios a fechas parciales.
- Auditoría de integridad: ID no vacío y único *en cada edición*, fechas válidas y ordenadas, código país y violencia válidos, `low,best,high` enteros. **Si `low<=best<=high` no se cumple para un evento estatal (tipo 1), bloquear y revisar**, no corregir ni truncar silenciosamente. Las anomalías de violencia no estatal o unilateral (tipo 2/3), que no pertenecen a este estimando, se cuentan y excluyen sin utilizar sus estimaciones.
- Código de estado: registrar recuento de categorías `code_status` para todos los eventos estatales de alta precisión dentro de cada ventana, y para los dos países foco; sensibilidad `Clear` usa exactamente `code_status.strip().casefold() == 'clear'`. Valores no reconocidos quedan documentados como tales, no adivinados.
- Para **2024–2026**, exigir que los totales `best` y las etiquetas mayo Q2/Q3, para `T=5`, coincidan con el informe congelado de sensibilidad anterior por país. En 2026, cotejar además `best` 90 días con el vector del experimento `candidate-reactivation-threshold-grid.json`.
- Publicar por país foco **solo** agregados de eventos, `low/best/high`, códigos `code_status` y etiquetas; nunca fichas ni descripciones de víctimas. Para todos los demás países, publicar solo conteos nacionales globales por versión para `T=5` (nº de positivos e inestables), no eventos individuales.
- No alterar jamás probabilidades prospectivas GEO2027, GEO2028, NEWCONF2027, ACD2027 ni emitir un nuevo vector de probabilidades. No certificar fecha original de publicación de Candidate.

## Criterios de interpretación

- **Robustez limitada dentro de la edición:** si `sum(low)>=5` la etiqueta supera el umbral para las tres estimaciones de fallecimientos, pero *solo en esa edición* y con las reglas anteriores.
- **Fragilidad por incertidumbre:** si `best>=5` pero `low<5` o `Clear-only best<5`, informar explícitamente; esto es un control de sensibilidad, **no una probabilidad de que ocurrió**.
- **Fragilidad por revisión:** Q2 y Q3 no son dos muestras independientes. Si cambian, el supuesto «acierto» no es estable; si coinciden, no certifica GED anual.
- **Top10**: publicar aciertos mínimo–máximo y esperanza bajo desempate uniforme, no atribuir habilidad individual a desempates por ID.
- Posteriormente: contrastar Candidate con GED anual 2024/25 y comprobar fechas de primera publicación (fuente archivada con sello temporal verificable). Para 2026 no existe aún GED anual definitivo; esperar a edición oficial.
- En caso de datos inválidos, resultados distintos del prerregistro o pérdida de integridad de fuente, bloqueo. Todos los informes son institucionales y no muestran datos personales.

Fuentes: [UCDP Candidate oficial](https://ucdp.uu.se/downloads/) y [Hegre et al. (2020)](https://doi.org/10.1177/2053168020935257), que advierten de revisiones de codificación y diferencias frente a GED final.

## Enmienda de integridad previa al cómputo de resultados (20-11-2026)

La primera ejecución se bloqueó al hallar en el CSV Q1 de 2024 un evento de **violencia unilateral (tipo 3)** con `low=43`, `best=44`, `high=43` (`id=517963`). Incumple el orden supuesto `low≤best≤high`, pero **su tipo queda fuera del resultado estatal (`type_of_violence=1`)**. El protocolo inicial bloqueaba por cualquier evento en toda la fuente. Se ha corregido **después de observar la anomalía**, antes de inspeccionar los resultados de incertidumbre: ahora registra en cada archivo `nonstate_invalid_bounds_excluded` y descarta todos los eventos tipo 2/3 (sin corregir cifras), pero **mantiene el bloqueo si el orden es incorrecto para cualquier registro estatal tipo 1**. Este cambio debe considerarse una enmienda explícita post inspección; no aporta información sobre los dos resultados 2026. La prueba adversarial verifica la cuarentena y que no se altera la suma estatal.
