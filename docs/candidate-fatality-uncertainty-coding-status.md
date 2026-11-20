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
- Auditoría de integridad: ID no vacío y único *en cada edición*, fechas válidas y ordenadas, código país y violencia válidos, `low,best,high` enteros. El protocolo original ordenaba **bloquear** cuando `low<=best<=high` no se cumpliera, pero el análisis de datos ha obligado a la enmienda documentada al final: **conservar las estimaciones oficiales como tres escenarios sin reordenar ni truncar, contar las anomalías y no afirmar un intervalo matemático**. Los valores negativos y errores de esquema siguen bloqueando. Las anomalías de violencia no estatal o unilateral (tipo 2/3), que no pertenecen a este estimando, se cuentan y excluyen sin utilizar sus estimaciones.
- Código de estado: registrar recuento de categorías `code_status` para todos los eventos estatales de alta precisión dentro de cada ventana, y para los dos países foco; sensibilidad `Clear` usa exactamente `code_status.strip().casefold() == 'clear'`. Valores no reconocidos quedan documentados como tales, no adivinados.
- Para **2024–2026**, exigir que los totales `best` y las etiquetas mayo Q2/Q3, para `T=5`, coincidan con el informe congelado de sensibilidad anterior por país. En 2026, cotejar además `best` 90 días con el vector del experimento `candidate-reactivation-threshold-grid.json`.
- Publicar por país foco **solo** agregados de eventos, `low/best/high`, códigos `code_status` y etiquetas; nunca fichas ni descripciones de víctimas. Para todos los demás países, publicar solo conteos nacionales globales por versión para `T=5` (nº de positivos e inestables), no eventos individuales.
- No alterar jamás probabilidades prospectivas GEO2027, GEO2028, NEWCONF2027, ACD2027 ni emitir un nuevo vector de probabilidades. No certificar fecha original de publicación de Candidate.

## Criterios de interpretación

- **Robustez limitada dentro de la edición:** si `sum(low)>=5`, y **no hay ningún evento de la ventana con orden low/best/high inconsistente**, la etiqueta supera el umbral en los escenarios examinados. Cuando sí hay anomalías, se informan los resultados por campo como escenarios independientes y **no se habla de cotas certificadas**.
- **Fragilidad por incertidumbre:** si `best>=5` pero `low<5` o `Clear-only best<5`, informar explícitamente; esto es un control de sensibilidad, **no una probabilidad de que ocurrió**.
- **Fragilidad por revisión:** Q2 y Q3 no son dos muestras independientes. Si cambian, el supuesto «acierto» no es estable; si coinciden, no certifica GED anual.
- **Top10**: publicar aciertos mínimo–máximo y esperanza bajo desempate uniforme, no atribuir habilidad individual a desempates por ID.
- Posteriormente: contrastar Candidate con GED anual 2024/25 y comprobar fechas de primera publicación (fuente archivada con sello temporal verificable). Para 2026 no existe aún GED anual definitivo; esperar a edición oficial.
- En caso de datos inválidos, resultados distintos del prerregistro o pérdida de integridad de fuente, bloqueo. Todos los informes son institucionales y no muestran datos personales.

Fuentes: [UCDP Candidate oficial](https://ucdp.uu.se/downloads/) y [Hegre et al. (2020)](https://doi.org/10.1177/2053168020935257), que advierten de revisiones de codificación y diferencias frente a GED final.

## Enmienda de integridad previa al cómputo de resultados (20-11-2026)

La primera ejecución se bloqueó al hallar en el CSV Q1 de 2024 un evento de **violencia unilateral (tipo 3)** con `low=43`, `best=44`, `high=43` (`id=517963`). Incumple el orden supuesto `low≤best≤high`, pero **su tipo queda fuera del resultado estatal (`type_of_violence=1`)**. El protocolo inicial bloqueaba por cualquier evento en toda la fuente. Se ha corregido **después de observar la anomalía**, antes de inspeccionar los resultados de incertidumbre: ahora registra en cada archivo `nonstate_invalid_bounds_excluded` y descarta todos los eventos tipo 2/3 (sin corregir cifras), pero **mantiene el bloqueo si el orden es incorrecto para cualquier registro estatal tipo 1 elegible en la ventana evaluada**. Este cambio debe considerarse una enmienda explícita post inspección; no aporta información sobre los dos resultados 2026. La prueba adversarial verifica la cuarentena y que no se altera la suma estatal.

### Segunda enmienda de elegibilidad (20-11-2026)

La reejecución halló además un evento **estatal tipo 1** en Q1 de 2024 (`id=514173`, `date_prec=4`, intervalo 1–31 de enero) con `low=50`, `best=32`, `high=10`. **Queda fuera del protocolo por precisión temporal insuficiente**. El control ahora distingue anomalías por causa de exclusión y recoge contadores `state_invalid_bounds_excluded_low_precision`, `state_invalid_bounds_excluded_outside_universe` y `state_invalid_bounds_excluded_outside_windows`. Solo los **eventos estatales de precisión 1/2 totalmente contenidos en ventanas predeclaradas y pertenecientes al universo canónico** quedan sometidos al bloqueo por orden inconsistente. Esto es una enmienda metodológica explícita posterior a la inspección de datos, no un arreglo de valores. El mismo caso, si tuviera precisión admitida y estuviera dentro de la ventana, seguiría bloqueando. No se publicará un resultado numérico mientras haya anomalías en el universo elegible.

### Tercera enmienda: fuentes oficiales con triples no monótonos también dentro de la ventana (20-11-2026)

La validación posterior encontró en Q1 de 2024 un evento **estatal de precisión 2 elegible** (`id=514686`, país 530) con `low=18`, `best=18` y `high=17`. La hipótesis de que **todos** los eventos oficiales satisfacen `low≤best≤high` es empíricamente falsa. El bloqueo total impediría cualquier análisis de la incertidumbre, a pesar de que el objetivo `best` original ya está publicado y congelado. Antes de calcular los resultados finales se sustituye la regla: el script no modifica los números, cuenta `eligible_nonmonotone_event_rows` y `nonmonotone_events` en las ventanas, y ejecuta **escenarios `low`, `best`, `high` individuales**, no intervalos garantizados. Los valores negativos en un evento evaluable, duplicados, fechas inválidas y fuentes con SHA distinto siguen bloqueados.

La conclusión solo podrá describir como robusto un país-ventana cuando sus eventos analizados **no tengan triples no monótonos** y supere el umbral en los escenarios pertinentes. La modificación es **posterior a examinar anomalías de 2024**, debe ser reproducida y no debe presentarse como un protocolo ciego o exactamente igual al inicial. Ningún cambio se ha efectuado en `best`, en las probabilidades históricas ni en las fuentes. El código en CI conservará esta historia de enmiendas, en lugar de ocultarla.

## Resultados originales reproducidos (20-11-2026)

La CI descargó **nueve CSV UCDP Candidate**, comprobó el SHA-256 contra los estudios anteriores y verificó los `best` de los **196 países de 2026** contra el benchmark congelado. El [informe completo](../data/candidate-fatality-uncertainty-code-status.json) contiene los 9 hashes, cada decisión de selección, tasas agregadas, triples originales `low/best/high`, estados de codificación, top10 sin reentrenamiento y contadores de estimaciones no monótonas.

### Desenlace de mayo, reactivación ≥5 fallecidos estatales registrados

| Año / vintage | Países Q1 `best<5` | `low>=5` | `best>=5` | `high>=5` | `Clear-only best>=5` |
|---|---:|---:|---:|---:|---:|
| 2024 Q2 | 161 | 2 | 2 | 2 | 1 |
| 2024 Q3 | 161 | 2 | 2 | 2 | 1 |
| 2025 Q2 | 160 | 4 | 5 | 6 | **0** |
| 2025 Q3 | 160 | 4 | 4 | 5 | **0** |
| 2026 Q2 | 155 | 2 | 2 | 2 | **0** |
| 2026 Q3 | 155 | 2 | 2 | 2 | **0** |

Estas cifras se refieren **solo a los países de cada año inicialmente por debajo de 5 muertes estatales registradas en Q1**. No equivalen a incidencia real ni confirman ausencia de conflictos. El filtro `Clear` es **una comprobación severa de codificación**, no el estándar por el que UCDP define los eventos definitivos.

### Kenia y Libia en mayo de 2026

| País | `low` | `best` | `high` | `Clear-only best` | Eventos estatales con fecha admitida | Estados de código |
|---|---:|---:|---:|---:|---:|---|
| Kenia | 12 | 12 | 16 | **0** | 6 | 4 `check type of violence`, 1 `check dyad`, 1 `clear` |
| Libia | 5 | 5 | 5 | **0** | 1 | 1 `check dyad` |

**Las estimaciones y las etiquetas anteriores coinciden exactamente en Q2 y Q3**. Los siete eventos de ambos países tienen triples `low/best/high` monótonos, de acuerdo con los contadores por país. La advertencia crítica procede de `code_status`: aunque Kenia cuenta con un registro `clear`, este no aporta suficientes fallecidos para alcanzar cinco. Libia depende íntegramente de un registro `check dyad`.

**Resultado del mismo modelo combinado original, sin nuevo entrenamiento**: de los diez países de mayor puntuación en 2026, obtiene **2/10** aciertos si el objetivo se mide con `low`, `best` o `high`, en Q2 y Q3. Con `Clear-only best`, obtiene **0/10**, porque **ningún** país del conjunto de riesgo supera el umbral con este filtro en 2026. La contabilidad incluye cotas exactas por empates, no atribuye mérito al orden de identificadores.

### También en el horizonte 90 días

La edición Q3 registra para Kenia **29** fallecidos `best` (29 `low`, 65 `high`, 16 `Clear-only best`) y para Libia **5** `best` (5 `low`, 5 `high`, **0 `Clear-only best`). El subconjunto de 155 países a riesgo de T=5 tiene **3 positivos `best`** a 90 días, pero solo **1 positivo `Clear-only best`**. La señal de Kenia permanece; la de Libia no supera el filtro `Clear`. Este es un endpoint de registros provisionales con precisiones restringidas, no de guerras nuevas.

### Anomalías de integridad, conservadas

El estudio ha observado triples no monótonos `low/best/high` en eventos originales de diversas versiones, **incluso en eventos estatales elegibles de otras regiones**. Se han conservado los números sin invertir, truncar ni corregir y se cuentan por archivo y país. Por ello `low` y `high` aquí son **escenarios derivados de los campos originales**, no cotas matemáticas garantizadas de todos los eventos de la base. Ninguno de los eventos admitidos que sustentan la comparación Kenia/Libia de mayo presenta esa anomalía.

### Decisión científica

**No promocionar el resultado de Kenia y Libia como dos alertas confirmadas.** Su interpretación depende de cómo se traten los eventos pendientes de comprobación, especialmente la atribución de actores y el tipo de violencia. Como explica la [investigación original de UCDP Candidate](https://doi.org/10.1177/2053168020935257), esos eventos pueden ser revisados, eliminados o confirmados durante el paso a GED anual. El filtro `Clear` puede ser demasiado estricto para un objetivo operativo, pero su efecto es demasiado grande para ignorarlo.

La siguiente fase útil no es elegir a posteriori un umbral o un modelo: debe analizar **Candidate→GED anual** sobre años ya resueltos, mantener el mismo estimando y conservar las etiquetas provisionales como una medida **diferente**. Después, solo emitir nuevas predicciones si existen fuentes oportunas con fecha de publicación original verificable. Ninguna predicción prospectiva nueva se ha emitido.
