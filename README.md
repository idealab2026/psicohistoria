# PSICOHISTORIA · IDEA LAB

Laboratorio público de investigación de sistemas complejos, fenómenos colectivos y evaluación de pronósticos.

**Estado actual: versión pública experimental, reconstruida de forma independiente.** El sitio incluye diez vistas navegables con formato oscuro, mapa de investigación, explorador de escenarios, evaluación probabilística, registro y hoja de ruta, y herramientas locales de preparación de hipótesis y guiones.

## Q-CANDIDATE · Cuatro cohortes Candidate→GED anual (20-11-2026)

El contraste con las primeras versiones GED anuales se ha extendido a
**2021 (GED 22.1) y 2022 (GED 23.1)**, manteniendo los resultados
2024/25 publicados anteriormente, sin reetiquetar fuentes
y con SHA-256 de **10 archivos** originales en los dos estudios.

**Indicador exploratorio:** en países cuyo Candidate Q1 registra
menos de 5 muertes estatales bien fechadas, los que superan
5 muertes del 1–30 de mayo aparecen así:

| Año | Candidate Q3 positivos | También positivos en GED anual |
|---|---:|---:|
| 2021 | 3 | **3/3** |
| 2022 | 1 | **1/1** |
| 2024 | 2 | **0/2** |
| 2025 | 4 | **1/4** |
| **Cuatro años** | **10** | **5/10** |

**La concordancia es temporalmente inestable:** los cuatro
positivos de 2021/22 se conservan, pero solo 1/6
de 2024/25. Esto impide tomar una tasa global
del indicador provisional como parámetro universal
de conversión a GED anual. No demuestra cambios
reales de guerras: hay diferencias de codificación,
revisión e inclusión. Tampoco permite certificar
habilidad prospectiva. A 90 días, mismo T=5,
la coincidencia positiva es **10/25** en 642
observaciones país-año a riesgo, con horizontes
solapados y países dependientes.

[Estudio, casos nacionales y limitaciones](docs/candidate-ged-2021-22-annual-resolution.md)
· [Informe congelado, trazabilidad y resumen a cuatro años](data/candidate-ged-2021-22-resolution.json)
· [Código y tests](scripts/audit_candidate_ged_2021_22.py).

## Q-CANDIDATE · ¿Se conservan las alertas en GED anual? (20-11-2026)

**Contraste implementado contra los archivos anuales oficiales UCDP GED 25.1
(2024) y GED 26.1 (2025), con ZIP originales y seis Candidate Q1/Q2/Q3
verificados por SHA-256.** Para el estimando exploratorio de reactivación
`>=5` muertes estatales bien fechadas entre el 1 y el 30 de mayo,
en países cuyo Candidate Q1 estaba por debajo de cinco, la
comparación encontró:

| Año | En riesgo | Positivos Candidate Q3 | Positivos GED anual | Positivos coincidentes |
|---|---:|---:|---:|---:|
| 2024 | 161 | 2 | 0 | 0 |
| 2025 | 160 | 4 | 1 | 1 |

**Solamente uno de seis indicadores positivos provisionales del mes
conserva la etiqueta en GED anual**: Indonesia 2025 (de 38
muertes registradas en Candidate a 14 en GED, bajo los mismos filtros).
Brasil y Bangladés 2024, así como Ecuador, Brasil y Libia 2025,
dejan de cumplir ese umbral en la edición GED del año.
En 2024 Bangladés había sido clasificado `Clear` en Candidate,
por lo que `Clear` **tampoco garantiza** la etiqueta anual.

Esta fragilidad del *indicador nacional en países de baja incidencia*
**NO implica que la mayoría de los acontecimientos Candidate sean
falsos**: aproximadamente **91 % de los IDs elegibles de mayo** coinciden
exactamente con registros GED del mismo año, y Candidate/GED tienen
criterios de inclusión diferentes. Los dos países de 2026 (Kenia,
Libia) siguen sin un GED anual 2026 de referencia.
**No se ha validado habilidad prospectiva ni disponibilidad
histórica original `as-of`**. Se preservan las cohortes fijadas.

[Resultados, matrices de confusión y límites](docs/candidate-to-ged-annual-resolution-protocol.md)
· [Informe verificable con 392 país-años y ocho SHA](data/candidate-to-annual-ged-resolution.json)
· [Código y reproducción](scripts/audit_candidate_to_annual_ged.py).

## Q-CANDIDATE · Estimaciones de fallecidos y calidad de codificación (20-11-2026)

**Hallazgo central de la auditoría de 9 fuentes originales Candidate**:
los **dos resultados** de reactivación ≥5 muertes estatales del
1–30 mayo de 2026, **Kenia y Libia**, mantienen el umbral bajo los
campos `low`, `best` y `high` en las ediciones Q2 y Q3. Pero
**ambos dejan de ser positivos** si el desenlace se restringe a
eventos `code_status=Clear` (0 positivos frente a 2), porque
dependen de registros marcados como pendientes de comprobar
tipo de violencia o actores (`check type of violence`, `check dyad`).
No significa que esos eventos sean falsos; Candidate es provisional
y la edición GED anual puede confirmar, revisar o descartar casos.

El estudio también detectó triples oficiales `low/best/high`
**no monótonos** incluso en eventos estatales elegibles de
otros periodos/países. Por ello los informes presentan estimaciones
como **escenarios sin manipular**, con anomalías contabilizadas;
no las describen como intervalos estadísticos fiables.
Los cambios metodológicos tras hallar esas irregularidades se
registran en el protocolo. No existe habilidad prospectiva
demostrada para esas dos alertas ni fecha de primera publicación
histórica independientemente acreditada.

[Estudio, enmiendas y conclusiones](docs/candidate-fatality-uncertainty-coding-status.md)
· [Informe congelado y nueve SHA](data/candidate-fatality-uncertainty-code-status.json)
· [Código y pruebas](scripts/audit_candidate_fatality_uncertainty.py).

## Q-CANDIDATE · ¿Sobreviven las reactivaciones a las revisiones? (19-11-2026)

Se ha comprobado **sin reentrenar modelos** el umbral de reactivación
para los días 1–30 de mayo en **nueve ediciones originales UCDP Candidate**
(Q1/Q2/Q3 de 2024, 2025, 2026), preservadas mediante SHA-256 y
con resultados exactos reproducidos en CI. El análisis fue motivado
por un resultado favorable del umbral ≥5 que ya se había examinado:
**es sensibilidad post selección, no validación independiente**.

**Hallazgo:** para ≥5 muertes estatales registradas, los positivos
en riesgo de 2026 son **2 en Q2 y los mismos 2 en Q3**
(Kenia y Libia); el top10 de la referencia combinada retiene
2/10 con ambas versiones, sin alterar el modelo. Pero
**en 2025 la misma etiqueta pierde 1 positivo (5→4)**
y la etiqueta ≥1 también pierde un caso en 2024 y 2025.
No se ha comprobado estabilidad frente a GED anual, fechas
originales de publicación ni vigencia prospectiva.

[Diagnóstico, límites y sensibilidad](docs/candidate-may-threshold-vintage-stability.md)
· [Informe congelado con 9 archivos SHA](data/candidate-may-threshold-vintage-stability.json)
· [Código de cotejo](scripts/audit_candidate_may_threshold_stability.py).

## Q-CANDIDATE · Grid de reactivación estatal de 1/5/10/25 muertes (19-11-2026)

**Nueva investigación exploratoria reproducida en diez ediciones originales UCDP Candidate**
de 2021, 2022, 2024, 2025 y 2026; 2023 se excluye de esta comparación por no tener
un acumulado Q1 enero–marzo comparable en el catálogo. El entrenamiento usa los
primeros cuatro años y se evalúa retrospectivamente en 2026 sin reajustar,
con horizontes de 30/90 días, umbrales predefinidos 1/5/10/25
y cuatro modelos sencillos (climatología, estado previo, otras violencias
y combinación). Las fuentes siguen sin tener **fecha original de publicación
as-of certificada**, y los positivos son registros Candidate provisionales,
no el comienzo de guerras ni daños finales.

**Hallazgos:** los positivos en riesgo de superar un nuevo umbral de 25
fallecidos son demasiado escasos (2026: 0/166 a 30d, 2/166 a 90d).
El umbral de cinco muertes genera 2/155 a 30d y 3/155 a 90d;
su modelo combinado logra Brier 0,010639 y 0,015598, respectivamente,
frente a 0,012754 y 0,019422 de climatología. El top10
histórico a 30d incluye los dos positivos, **pero representa
un resultado no ciego y de un solo año, no una habilidad prospectiva**.
No optimizar ni promocionar el umbral favorable después de observarlo.

[Estudio, definiciones y límites](docs/candidate-reactivation-threshold-grid-protocol.md)
· [Informe completo con 196 observaciones 2026 y diez SHA](data/candidate-reactivation-threshold-grid.json)
· [Script reproducible](scripts/experiment_candidate_reactivation_grid.py).

## Q-CANDIDATE · Alertas de escalada: sensibilidad de versiones y empates (19-11-2026)

**Nuevo estudio reproducible sobre 9 vintages Candidate oficiales, sin emisión prospectiva:** en el conjunto inicial de países con menos de 25 fallecidos estatales registrados de enero a marzo hubo solo **1 caso positivo de 505 países-año** a 30 días (mayo, 2024–2026), incluso usando dos ediciones posteriores de Candidate. A 90 días en 2026 hay solo **2 positivos de 166 países**, Kenia e Indonesia, ambos incluidos en un grupo de **21 países con la misma probabilidad** para el modelo de volumen. En este grupo el supuesto acierto `top10` depende de un desempate arbitrario y admite **0 a 2 aciertos**; no identifica países individuales entre los 21. Una vigilancia sobre todo ese grupo produciría **19 falsas alertas/21** en esta muestra, para este endpoint estricto.

No hay todavía evidencia de un clasificador con habilidad prospectiva para nuevos cruces del umbral; la señal retrospectiva observada sigue refiriéndose principalmente a la **continuación de violencia ya registrada**. La fecha de publicación original de cada vintage sigue sin certificarse.

[Estudio con inferencias y límites](docs/candidate-onset-label-revision-tie-protocol.md) · [Informe agregado y nueve hashes originales](data/candidate-onset-label-revision-ties.json) · [Código y cotas de empates](scripts/audit_candidate_onset_label_stability.py).

## Q-CANDIDATE · Primer experimento retrospectivo 30/90 días (19-11-2026)

Se ha ejecutado y congelado un primer **holdout temporal de 2026** sobre los
196 países, entrenando los tres modelos de referencia solamente con los
vintages de 2024–2025, para estimar `>=25` muertes estatales *registradas*
en UCDP Candidate con precisión temporal 1–2 en una ventana posterior.
El origen usa el acumulado enero–marzo y **abril se deja sin observar**:
se evalúa 1–30 mayo (30 días) y 1 mayo–29 julio (90 días). **La fecha
original de publicación de los archivos no está certificada; la evaluación
no es retrospectiva as-of validada ni una emisión prospectiva.**

**Brier 2026 (menor es mejor):** 30 días: global 0,07971;
persistencia 0,03919; volumen reciente **0,03910**.
90 días: global 0,11887; persistencia **0,03141**; volumen 0,03163.
El resultado útil científicamente es que el volumen reciente identifica
bien *persistencia* en este histórico; **no demuestra anticipación de
nuevos conflictos**: 0/166 entradas al umbral a 30 días y
solo 2/166 a 90 días (Kenia e Indonesia en la muestra Candidate).
Se han detectado además códigos de precisión no documentados,
con tratamiento conservador y prueba adversarial.

[Protocolo, tabla de métricas y límites](docs/candidate-30-90-baseline-holdout-protocol.md)
· [196 registros retrospectivos, parámetros y SHA](data/candidate-30-90-baseline-holdout.json)
· [Código reproducible](scripts/experiment_candidate_30_90_holdout.py).

## UCDP Candidate · Revisión de datos históricos Q2→Q3, 2024–2026 (19-11-2026)

**Primer contraste oficial reproducido de seis archivos UCDP Candidate, SIN pronóstico emitido.** Para los mismos registros enero–junio de 2024–2026, las ediciones de septiembre aportan **3.359 IDs adicionales**, dejan fuera **1.042 IDs** presentes en junio y modifican el número de fallecidos `best` de **431 de los 35.989 eventos emparejados**. En 2024 y 2025 cambia la clasificación semestral ≥25 fallecidos estatales de un país al revisar los datos. Estas son **revisiones de dos versiones** de información provisional, no acontecimientos futuros ni evidencia de mayor precisión. No se ha certificado la fecha original de cada primera publicación.

[Informe con fuentes SHA-256 y límites](docs/candidate-q2-q3-vintage-revisions.md) · [Censo agregado congelado](data/candidate-q2-q3-vintage-revisions.json) · [Código de reproducción](scripts/audit_candidate_q2_q3_vintages.py). La CI exige el mismo resultado con los seis archivos originales antes de aceptar cambios.

## NUEVA LÍNEA · Predicción experimental de 30/90 días con UCDP Candidate (19-11-2026)

**Estado verificable: puerta de elegibilidad de ediciones implementada; CERO pronósticos emitidos, CERO resultados resueltos.** El objetivo es llegar a predicciones de escalada en un horizonte práctico, pero primero debe probarse la disponibilidad original de las fuentes y su calidad temporal. El catálogo UCDP consultado el 19/11/2026 muestra como última edición Candidate de 2026 la de septiembre (26.0.9) y el acumulado enero–septiembre (26.01.26.09); el catálogo no demuestra por sí solo las fechas originales de publicación.

**Primer cotejo con bytes oficiales:** UCDP Candidate 26.01.26.09 tiene **16.633 registros** y SHA-256 `134da9b3df08b65266802c4b662e572f396c70c92ab62297319be657540bcede`. El parser institucional reproduce **16.609 filas admisibles**, **9.960 estatales** y **24 eventos multidiarios que atraviesan septiembre→octubre puestos en cuarentena**; no son resultados futuros ni predicciones. [Informe oficial agregado](data/candidate-2026q3-source-audit.json).

El programa `scripts/check_ucdp_candidate_asof.py` bloquea archivos no oficiales, fechas futuras, cobertura insuficiente para 90 días, datos obsoletos (más de 45 días respecto a emisión), duplicados, cronologías incoherentes y SHA incorrectos. **Un archivo elegible no constituye una predicción ni una validación científica.** La combinación origen 19/11/2026 / última cobertura 30/09/2026 ya supera el límite fijado (50 días): no se emitirán riesgos fingiendo que esos datos son actuales. El proceso incluye tests adversariales sintéticos y nueva comprobación institucional de privacidad.

[Protocolo completo y siguientes hitos](docs/candidate-30-90-day-asof-protocol.md) · [Auditor de edición as-of](scripts/check_ucdp_candidate_asof.py) · [Pruebas](scripts/test_check_ucdp_candidate_asof.py) · [UCDP Candidate — fuente](https://ucdp.uu.se/downloads/).

## GEO2027 · Auditoría de interpretación oficial: «cero codificado» no significa «sin violencia» (16-11-2026)

**Resultado científico relevante del manual oficial UCDP OrganizedViolenceCY 26.1:** la etiqueta del laboratorio se refiere a **`sb_total_deaths_best >=25` según UCDP**, no a la existencia de cualquier guerra, ataque ni víctimas reales. **Un cero codificado de fallecidos no prueba ausencia de violencia**: el conjunto omite incidentes de díadas/actores aún no incluidos bajo sus reglas de umbral. El campo `sb_exist` indica existencia de algún evento estatal recogido, y **no es equivalente** al recuento de muertes ni al estado «≥25» del modelo.

He contrastado las **cuatro fuentes oficiales 23.1/24.1/25.1/26.1 por SHA** (6.544 / 6.740 / 6.936 / 7.132 filas) con la columna de existencia estatal y las 196 claves GWNO congeladas. **Desde 2011 las cuatro series contienen filas explícitas de los 196 estados de la cohorte 2027**; antes de ese año no deben fabricarse países que aún no existían.

| Último año de cada edición | Filas expresas de la cohorte | Cero muertes codificadas | 1–24 | ≥25 | Ceros con `sb_exist=1` |
|---|---:|---:|---:|---:|---:|
| 2022 · 23.1 | 196 | 145 | 14 | 37 | 0 |
| 2023 · 24.1 | 196 | 150 | 12 | 34 | **1** |
| 2024 · 25.1 | 196 | 153 | 8 | 35 | 0 |
| **2025 · 26.1** | **196** | **154** | **8** | **34** | **0** |

En 2023 hay un caso real **`sb_total_deaths_best=0` y `sb_exist=1`** (persistente en las ediciones posteriores). Para 2022, una revisión de UCDP 23.1→26.1 cambia la clasificación de cero codificado de **un país** y la bandera `sb_exist` de **dos**. Las ediciones se solapan y **no son muestras independientes**.

**Implicación práctica:** el requisito 196/196 de la evaluación futura tiene precedente histórico desde 2011, pero **la primera edición oficial completa de 2027 aún debe verificarse**. Si falta una fila, el programa no puede convertirla a cero. Se mantiene el mismo objetivo, las tres emisiones de 196 países y las 15 alertas SHA-congeladas. **Ningún resultado oficial 2027 está disponible ni se ha reemitido ningún pronóstico.**

[Informe de auditoría y referencia oficial](docs/geo2027-ucdp-zero-coding-riskset-audit.md) · [Verificación de los cuatro datasets por edición y año](data/geo2027-ucdp-zero-coding-riskset-audit.json) · [Script y pruebas](scripts/audit_geo2027_ucdp_zero_coding.py).

## GEO2027 · Puerta de resolución oficial y evaluación prospectiva verificable (16-11-2026)

**Estado certificado: `NOT_READY`.** Las tres emisiones ya registradas sobre los **196 países** para 2027 (GEO original, primera sombra LOG1P y global-only matched α0/α1) permanecen **inmutables y sin resultados oficiales**. El nuevo programa **no emite otro modelo**: prepara y prueba cómo se puntuará exactamente la primera edición **oficial y completa** de UCDP OrganizedViolenceCY correspondiente a 2027.

**Condiciones obligatorias antes de puntuar:** solo a partir de 2028; archivo ZIP/CSV de país-año con SHA-256 verificado; **196 filas explícitas de 2027** coincidentes con los GWNO congelados; ausencia/duplicado/valor inválido implica **bloqueo, nunca imputación a cero**; revisión humana documentada del archivo y la secuencia de ediciones para justificar que sea la **primera edición completa**. El programa valida la ficha y la cobertura, pero no puede demostrar por sí solo la autenticidad oficial ni la prioridad cronológica de la edición. La evidencia editorial debe comprobarse externamente antes de presentar una evaluación como oficial.

Una vez superados los requisitos, se publicarán juntos **Brier y log-loss de cinco brazos** sobre los mismos 196 países, con la **comparación principal previamente registrada**: Brier(global-only α1) − Brier(LOG1P original), cuyo signo se desconocerá hasta que haya resultados. También se reproducirá exactamente la atribución de Brier país a país fijada antes del desenlace, sin escoger modelos, penalizaciones o umbrales a posteriori.

Se han añadido **12 pruebas con etiquetas exclusivamente sintéticas** para errores de fuente, fecha, cobertura, 24/25 muertes, duplicados, columnas CY, ZIP y reconstitución matemática de la diferencia primaria. Ningún Brier sintético se conserva como resultado real. GitHub Actions y Pages requieren que el [estado `NOT_READY` auditable](data/geo2027-full196-resolution-readiness.json) sea byte idéntico al verificado desde las tres emisiones y las 15 alertas SHA-fijadas.

[Protocolo íntegro y límites](docs/geo2027-full196-official-resolution-readiness.md) · [Validador futuro de edición oficial](scripts/resolve_geo2027_first_complete_official.py) · [Pruebas sintéticas](scripts/test_resolve_geo2027_first_complete_official.py).

## GEO2027 · Diagnóstico de regularización local Markov y revisiones UCDP (16-11-2026)

**Estudio nuevo, sin reemitir pronósticos:** se han reproducido **8 combinaciones origen–edición** de UCDP 23.1–26.1 y **5 comparaciones solapadas de revisiones** con los **196 identificadores originales**, cortando todos los historiales en el año de origen. Se ha verificado la reproducción matemática exacta del primer GEO2027 (2025→2027), manteniendo sus SHA y los de las dos sombras y las 15 alertas.

En los **154 países con 0 muertes estatales en el origen de 2025**, la amplitud de probabilidades del Markov bruto H2 pasa de **0,21 puntos porcentuales** sin usar las transiciones locales (`w=0`) a **11,20 pp** dando un cuarto de peso local (`w=0,25`), **18,45 pp** con medio peso y **27,10 pp** con peso completo. La información histórica propia bajo shrinkage 20 representa en promedio **62,25 %** del cálculo de transición desde estado inactivo cuando `w=1`.

**Pero esa diferenciación también es sensible a revisiones de fuentes:** al comparar el mismo origen de 2022 desde UCDP 23.1 a 26.1, el mayor cambio individual crece de **0,41 pp con `w=0`** a **5,36 pp con `w=1`**; la revisión media absoluta pasa de **0,064** a **0,130 pp**. Los cinco pares muestran un aumento de la media y los máximos, pero **el percentil 95 no es monótono**: la sensibilidad se concentra en pocos casos.

**No equivale a mejora demostrada del Brier:** son probabilidades del componente Markov sin calibrar, con pesos preenumerados para sensibilidad y ediciones históricas retrospectivamente revisadas. No se ha seleccionado `w`, no se ha entrenado ni publicado ningún nuevo candidato GEO2027 y **no hay resultados oficiales 2027**. La comparación prospectiva principal sigue siendo la ya registrada entre las dos sombras de 196 países.

[Informe y límites metodológicos](docs/geo2027-markov-partial-pooling-vintage-stability.md) · [Ocho snapshots y cinco pares de revisiones](data/geo2027-markov-partial-pooling-vintage-stability.json) · [Código científico](scripts/diagnose_geo2027_markov_partial_pooling.py) · tests de no-leakage y GitHub Actions con fuentes SHA-fijadas.

## GEO2027 · Auditoría de desacuerdo entre emisiones prospectivas congeladas (16-11-2026)

**Nuevo control ex ante, sin resultados oficiales de 2027:** se han comparado las **196 probabilidades exactas** de la primera sombra LOG1P (SHA `52686923…`) con las 196 de la nueva emisión Markov global-only matched α=1 (SHA `251595a1…`), sin modificar ningún pronóstico ni las 15 alertas originales.

El efecto central es la **pérdida de heterogeneidad del riesgo para los 154 países con cero muertes estatales en 2025**: la primera sombra LOG1P asigna un intervalo de **1,37 % a 22,62 %**, pero el global-only casi no discrimina (**3,50 % a 3,59 %**). Retirar el historial nacional evita dependencia de sus transiciones locales, pero también elimina una señal potencialmente útil. Es imposible saber todavía si esa heterogeneidad histórica representaba información o ruido.

| Indicador sobre 196 países | Resultado del contraste entre sombras |
|---|---:|
| Cambio medio **absoluto** de probabilidad por país | **2,87 pp** |
| Países cuyo riesgo cambia al menos 5 puntos porcentuales | **27** |
| Países cuyo riesgo cambia al menos 10 puntos porcentuales | **9** |
| Solapamiento de top 10 de riesgo entre países inicialmente inactivos | **6/10** |
| Solapamiento de top 5 entre países inicialmente activos | **2/5** |
| Países de 2025 con 1–24 muertes donde **α=0 y α=1 realmente difieren** | **8** |

La suma de probabilidades de países activos pasa de **35,9840** (LOG1P original) a **36,2157** (global-only), apenas **+0,2317 países esperados**, a pesar de desacuerdos individuales grandes. **Burundi** presenta la mayor diferencia absoluta, desde 22,62 % (LOG1P original) hasta 3,50 % (global-only). Los rankings son diagnósticos de las probabilidades ya emitidas, **no listas nuevas de alertas ni predicciones emitidas nuevamente**.

El informe añade para cada país la identidad exacta de la diferencia futura Brier según que en 2027 se observe o no el umbral de 25 muertes. Su evaluador se ha cotejado **solo con etiquetas sintéticas**, nunca con resultados 2027 supuestos; la evaluación real seguirá el contrato precomprometido del primer archivo oficial UCDP con 196 etiquetas completas. No se emiten p-valores IID ni se declara mejor modelo antes de observarlo.

[Análisis y límites científicos](docs/geo2027-global-only-issued-disagreement.md) · [196 diferencias y sensibilidad a futuro Brier](data/geo2027-global-only-issued-disagreement.json) · [Código y tests de identidad](scripts/diagnose_geo2027_issued_disagreement.py) · GitHub Actions comprueba igualdad exacta del informe derivado de los cuatro artefactos SHA-fijados.

## GEO2027 · Nueva emisión prospectiva independiente sobre los 196 países (16-11-2026)

**Primera emisión completa:** comparador Markov **global-only con calibración LOG1P emparejada y país excluido**, generado sobre UCDP OrganizedViolenceCY **26.1 hasta 2025**, con horizonte 2027 y **196 países originales**. Se han publicado dos brazos independientes pero predefinidos: **α=0**, sin pendiente de intensidad subumbral, y **α=1**, con pendiente continua completa. Para cada país se reajusta su calibrador logístico sin utilizar **ninguna de sus etiquetas históricas ni transiciones dentro de los priors de entrenamiento**; cada fila del resto excluye también las transiciones del propio país de la fila. El estado y muertes del país en 2025 sí son observables al emitir el pronóstico.

| Emisión congelada para 2027 | Suma de probabilidades de superar 25 muertes estatales |
|---|---:|
| Original GEO2027, sin modificar | **33,6254** |
| Sombra LOG1P original, sin modificar | **35,9840** |
| **Nueva sombra global-only α=0** | **35,5550** |
| **Nueva sombra global-only α=1** | **36,2157** |

Las sumas **no son resultados ni aciertos**: el primer informe oficial completo de los hechos de 2027 todavía no existe. Se mantiene un **contrato de evaluación prospectiva principal**: Brier sobre los mismos **196 GWNO**, global-only α1 **menos** la sombra LOG1P original, usando exclusivamente la **primera edición completa** de UCDP con etiquetas 2027 oficiales; las faltantes nunca se imputan como cero. Los dos nuevos brazos, el GEO original, la sombra LOG1P original y el control solo-intercepto tendrán Brier/logloss publicados juntos, sin seleccionar a posteriori un campeón ni invocar independencia IID de países.

**Anclaje de integridad:** el primer archivo completo de 196 países apareció en el commit institucional público `52ab9ffe7d49e4574b61a9f6a35c57cf7b43082d`, registrado por GitHub el **2026-11-16 19:49:19 UTC**, con SHA-256 **`251595a12758e006cf21dabbb9771e10b5961c469a5317d6b2b1c5de227f3697`** (metadatos GitHub, no notarización independiente). El modelo anterior GEO de 196, la primera sombra LOG1P de 196 y las **15 alertas originales** conservan exactamente sus SHA. No se reemiten esas predicciones.

**Advertencia científica:** las formas funcionales y λ=5 fueron estudiadas después de conocer resultados históricos 2017–2025; por tanto la supuesta mejora retrospectiva es exploratoria. Esto sí constituye **una nueva predicción anterior al resultado de 2027**, aunque **su capacidad de predicción prospectiva está pendiente de comprobar**.

[Protocolo y limitaciones](docs/geo2027-global-only-matched-prospective.md) · [Emisión nueva de 196 países](data/forecast-2027-global-only-matched-shadow.json) · [Manifiesto SHA y primer commit](data/forecast-2027-global-only-matched-manifest.json) · [Código reproducible](scripts/prepare_geo2027_global_only_matched_shadow.py) · auditoría de integridad y función de evaluación futura `scripts/audit_geo2027_global_only_matched_issue.py`.

## GEO2027 · Calibrador LOG1P reentrenado con Markov global-only emparejado (16-11-2026)

**Corregido el desajuste de distribución de la PR #98:** las probabilidades del Markov H2 global-only del país evaluado ya no se pasan a una regresión LOG1P aprendida sobre offsets locales. En la nueva PR se **excluyen todas las etiquetas históricas del país y sus transiciones del prior global**, y para cada fila de aprendizaje de otro país se excluyen además las transiciones de ese país de su propio prior. Los coeficientes de LOG1P se reentrenan con esos offsets global-only, respetando el corte H2 de etiquetas **t−2** y features **t−4**.

Las cuatro fuentes oficiales SHA-verificadas reconstruyen **143 pronósticos por país excluido**, en 13 bloques año–edición y 9 años distintos.

| Año UCDP 26.1 | Brier α1 subumbral, global-only **sin recalibrar** | Brier α1 subumbral, global-only **matched** | ΔBrier anual α1−α0 matched |
|---|---:|---:|---:|
| 2017 | **0,20059** | 0,20087 | −0,000044 |
| 2024 | 0,10896 | **0,09508** | **−0,002242** |
| 2025 | **0,07964** | 0,08705 | +0,000531 |

La calibración emparejada baja el Brier de α1 en **7 de 9 años (2018–2024)** y lo eleva en **2017 y 2025**. Ninguno de los 13 bloques revisados invierte el signo de α1−α0 respecto al **global-only no emparejado**. En 2017 el global-only sigue favoreciendo α1; al conservar el Markov original con historia nacional el signo era el contrario. La mejora **no es uniforme ni demuestra superioridad prospectiva**.

**Limitación:** las cifras de Brier absoluto se refieren **solo a los países con 1–24 muertes al origen**, no a un backtest cruzado de todos los 196 países. La familia λ=5 y los alfas se fijaron en investigaciones que ya habían examinado históricos; las cuatro ediciones UCDP no son réplicas independientes. **No hay un modelo ganador ni emisión nueva**; permanecen SHA idénticas las 196 GEO originales, las 196 LOG1P y las 15 alertas de 2027, sin outcomes oficiales resueltos.

[Documento metodológico y resultados anuales](docs/geo2027-log1p-matched-global-only-calibration.md) · [Informe completo de los 143 casos](data/geo2027-log1p-matched-global-only-calibration.json) · [Código y reproducción](scripts/experiment_geo2027_log1p_matched_global_only.py) · tests y CI institucional.

## GEO2027 · Influencia del historial nacional Markov frente al prior mundial (16-11-2026)

**Resultado del siguiente experimento sobre los 143 países-bloque subumbrales ya evaluados:** se mantienen fijos los coeficientes de calibración LOG1P aprendidos *sin ninguna etiqueta histórica del país evaluado*, pero se comparan tres probabilidades Markov H2 calculadas al origen: (1) original global + local; (2) prior global sin el país, con su propia historia local; (3) prior global sin el país **y sin sus transiciones locales**, aunque el estado del país en el origen sigue siendo conocido.

| Año retrospectivo UCDP 26.1 | Diferencia Brier α1−α0 con Markov original | Excluir solo contribución al prior mundial | Excluir también transiciones locales |
|---|---:|---:|---:|
| **2017** | **+0,000121** | +0,000120 | **−0,000053** |
| **2024** | −0,000821 | −0,000826 | **−0,001144** |
| **2025** | +0,000635 | +0,000633 | **+0,000093** |

**Hallazgo:** la auto-influencia del país sobre el prior de transiciones mundial es marginal (desplazamiento Markov absoluto medio **0,015–0,022 pp** en estos tres años), mientras su **historial de transiciones local** puede alterar notablemente el pronóstico (diferencias absolutas medias **4,40–6,89 pp**, con extremos por encima de 20 pp). Al retirar lo local, **2017 invierte el signo Brier**, también en las cuatro ediciones UCDP del año; 2025 reduce la desventaja relativa de LOG1P alrededor de **85 %** sin cambiar signo. El caso más relevante para 2017 es **Israel**; en 2024 las alteraciones de Angola y Burundi tienen sentidos distintos porque los resultados futuros de esos dos países también difieren.

**No es un modelo cold-start validado:** el coeficiente logístico se entrenó con offsets Markov de otros países **que sí incluían historia local**. El tercer escenario lo reutiliza con otro tipo de offset, de modo que puede generar desajuste de calibración. Es una **ablación mecanística retrospectiva**, no 13 réplicas independientes, ni prueba prospectiva de utilidad, ni sustitución de la sombra de 2027. La penalización LOG1P y los α fueron investigados después de conocer parte del histórico. **Las 196 predicciones GEO, las 196 LOG1P y las 15 alertas originales se mantienen byte idénticas; no se ha puntuado ningún resultado oficial 2027.**

[Metodología y resultados históricos](docs/geo2027-log1p-markov-country-history-ablation.md) · [Informe por año, país y escenario](data/geo2027-log1p-markov-country-history-ablation.json) · código `scripts/experiment_geo2027_log1p_markov_country_history_ablation.py` · auditoría reproducible GitHub Actions.

## GEO2027 · Transferencia del calibrador LOG1P entre países (16-11-2026)

**Nueva investigación publicada:** reentrenamiento logístico **excluyendo todas las filas históricas del país evaluado** antes de puntuar el efecto de conservar (α=1) o desactivar (α=0) la señal de intensidad estatal subumbral (1–24 muertes en el origen). Se conserva el Markov H2 original —con la historia pre-origen del país—; por tanto esto es **transferencia internacional del calibrador**, no predicción de países sin historial ni reestimación cold-start del Markov.

Se han reproducido **143 exclusiones del historial de calibración** en **13 bloques año–edición**, correspondientes a **9 años distintos**. En UCDP 26.1, **ninguno de los nueve años cambia de signo** respecto al modelo con todos los países presentes:

| Objetivo | Países subumbrales comprobados | ΔBrier α1−α0 con calibración completa | ΔBrier con calibrador entrenado sin cada país |
|---|---:|---:|---:|
| 2017 | 9 | +0,000111 | +0,000121 |
| 2024 | 15 | −0,000788 | −0,000821 |
| 2025 | 12 | +0,000620 | +0,000635 |

2018–2023 también mantienen la dirección de su contraste; repetir 2017 con UCDP 23.1/24.1/25.1 y 2024 con 25.1 no produce inversiones. En casos influyentes, **Israel (2017)** sigue perjudicando la señal completa, **Angola (2024)** la favorece, y **Uganda (2025)** vuelve a perjudicarla incluso sin sus propias etiquetas históricas dentro del calibrador.

**Conclusión limitada:** el signo anual no depende únicamente de que el país evaluado aporte sus propias observaciones históricas al modelo logístico. Eso **no elimina la dependencia de pocos países en el Brier**, la fragilidad ante revisiones de muertes, ni convierte datos históricos ya estudiados en una prueba prospectiva. El Markov sí usa la historia del país, el ridge λ=5 se seleccionó a posteriori y los 13 bloques son correlacionados. **Ningún modelo nuevo emitido; las 196 GEO originales, las 196 LOG1P y las 15 alertas para 2027 permanecen idénticas.**

[Metodología y resultados detallados](docs/geo2027-log1p-subthreshold-country-block-transfer.md) · [Informe fuente-auditado por país](data/geo2027-log1p-subthreshold-country-block-transfer.json) · [Script](scripts/experiment_geo2027_log1p_country_block_transfer.py) · GitHub Actions de pruebas de no-leakage y reproducción exacta.

## GEO2027 · Causas contables de las inversiones Brier en 2017 y 2025 (16-11-2026)

**Hallazgo fundamental del estudio anual**: al contrastar las dos variantes LOG1P α=1 (pendiente continua completa entre países inactivos) y α=0 (sin esa pendiente), **todos los países de origen con 0 muertes y todos los países de origen con ≥25 tienen exactamente el mismo pronóstico en ambas**. Por tanto, **solo los países que tenían de 1 a 24 muertes estatales best al origen pueden cambiar el Brier comparativo**. Son una minoría y su influencia en el score agregado es considerable.

| Objetivo retrospectivo, UCDP 26.1 | Países que determinan la comparación α1−α0 | Países de estos que cruzan 25 en el objetivo | Signo del Brier |
|---|---:|---:|---|
| **2017** | **9 de 196** | 2 | α0 mejor; `+0,000111` |
| **2024** | **15 de 196** | 2 | α1 mejor; `−0,000788` |
| **2025** | **12 de 196** | 1 | α0 mejor; `+0,000620` |

**2017**: Israel, origen 10 muertes, permanece inactivo y provoca un perjuicio en la pérdida cuadrática de **+0,049619** (antes de dividir entre 196). Sin Israel en el cálculo de la métrica, sin reentrenar, **el signo cambia**. **2024**: Angola y Sudán del Sur, con 20 y 23 muertes de origen, cruzan el umbral; su mejora de puntuación supera los errores de 13 países que no se activan. Sin Angola, **el signo cambia**. **2025**: Uganda, Armenia y Arabia Saudí concentran buena parte de los errores; Sudán del Sur es el único caso del grupo de 1–24 con ganancia por cruzar 25. **Omitir un solo país no invierte** el signo de ese año. Ninguna de las cuatro ediciones de UCDP disponibles cambia el signo de las contribuciones individuales del conjunto de 2017, ni las dos ediciones de 2024; **2025 solo dispone de una edición**.

El script certifica la identidad matemática de Brier por país, los 30 bloques año-edición y cortes de entrenamiento H2 `t−2`, con las cuatro fuentes SHA-verificadas. **Estos análisis no constituyen causalidad política, evidencia confirmatoria nueva, años originalmente emitidos ni 30 réplicas independientes**; la especificación λ=5 y el diseño α surgieron tras examinar parte del histórico. No se modifican las **196 predicciones originales, las 196 de la sombra 2027 ni las 15 alertas**; cero resultados 2027 resueltos.

[Documento con países y descomposición exacta](docs/geo2027-log1p-annual-country-reversals.md) · [Informe completo por año y versión](data/geo2027-log1p-country-year-reversal-attribution.json) · código `scripts/diagnose_geo2027_log1p_annual_country_reversals.py` y pruebas reproducibles con GitHub Actions.

## GEO2027 · Estabilidad anual LOG1P con validación temporal de horizonte 2 (16-11-2026)

**Nuevo resultado** de un estudio anual exhaustivo en las cuatro ediciones oficiales UCDP, con cortes temporales estrictos: para cada objetivo histórico `t` se ajusta el coeficiente logístico **solo hasta etiquetas `t−2`**, y los predictores de esas etiquetas se forman con corte `u−2`, **sin utilizar el año `t−1` ni el resultado `t` durante el ajuste**.

La comparación entre conservar toda la pendiente de intensidad continua LOG1P en países inactivos (α=1) y eliminarla (α=0) muestra la siguiente dirección de Brier, tomando la edición más reciente UCDP 26.1:

- **7 años favorecen α=1:** 2018, 2019, 2020, 2021, 2022, 2023 y 2024.
- **2 años favorecen α=0:** 2017 y 2025.
- **0 de 8 años con ediciones revisadas sufren inversión de signo de Brier** al compararse con las otras versiones oficiales, aunque las magnitudes cambian: en 2022 el beneficio α=1 se reduce aproximadamente 5,4 veces al pasar de la edición 23.1 a la 26.1.
- **9 años objetivo diferentes** (2017–2025), presentados en 30 bloques año-edición (6+7+8+9); las cuatro versiones de un año **no son cuatro experimentos independientes**.

El Brier anual medio UCDP 26.1 es **0,037980** con α=1 frente a **0,038576** con α=0. **No es una prueba de habilidad predictiva prospectiva:** las ediciones son fuentes retrospectivamente revisadas, λ=5 fue escogido en 2026 con parte del histórico ya conocido y los resultados 2024/25 se habían examinado. La cobertura histórica faltante se excluye y no se rellena como ausencia de conflicto; cada año informa número de países directamente observados del universo de 196.

**Estado:** la evidencia histórica favorece la señal continua en la mayoría de años, pero la ventaja varía y **se invierte en 2025**. No se modifica ni se reemite la primera sombra de 2027 ni las 15 alertas originales. Ningún outcome oficial 2027 se ha resuelto.

[Protocolo y resultados detallados](docs/geo2027-log1p-rolling-year-vintage-stability.md) · [Informe por año y versión, con 30 bloques](data/geo2027-log1p-rolling-year-vintage-stability.json) · reproductor `scripts/experiment_geo2027_log1p_rolling_year_vintage.py` · pruebas de no-leakage y gate institucional de GitHub Actions.

## GEO2027 · Frontera de robustez editorial vs Brier histórico del LOG1P (16-11-2026)

**Investigación de compromiso, no sustitución de la sombra prospectiva**: se han medido cinco variantes fijas que atenúan exclusivamente la pendiente LOG1P del grupo de países con menos de 25 muertes de violencia estatal en el origen (**α=0, 0,25, 0,5, 0,75, 1**). Se conservan intactos el intercepto, pendiente del grupo activo y offset Markov originales; α=1 reproduce exactamente el archivo LOG1P 2027 y los Brier históricos previamente publicados.

| Pendiente inactiva | Brier histórico conjunto 2024/25 | Banda media hipotética ±10 muertes en la emisión 2027 | Países garantizados del top-10 de entrada contrafactual |
|---|---:|---:|---:|
| **0 %** | 0,037815 | **0,082 pp** | **10/10** |
| 25 % | 0,037655 | 0,658 pp | 6/10 |
| 50 % | 0,037512 | 1,353 pp | 5/10 |
| 75 % | 0,037412 | 2,187 pp | 3/10 |
| **100 % · sombra LOG1P emitida** | **0,037393** | 3,178 pp | 2/10 |

**Atenuar por completo la señal en los inactivos reduce aproximadamente un 97,4 % la sensibilidad media a esta perturbación ±10**, con un empeoramiento de **1,1 % del Brier** en dos años reutilizados de forma exploratoria. El balance **se invierte por año**: 2024 favorece α=1 y 2025 α=0. El top-5 de resolución para el grupo activo mantiene 3/5 puestos garantizados en todas las variantes, porque su pendiente no cambia.

**No se ha elegido ni emitido ningún modelo nuevo:** los datos históricos 2024/25 se habían inspeccionado, el periodo 2018–20 ya sirvió para selección de hiperparámetros, y ninguna banda hipotética es un intervalo de confianza. Los cinco puntos son no dominados sobre estos dos ejes exploratorios; la capacidad predictiva prospectiva de 2027 sigue sin resolver. Las **196 probabilidades originales, las 196 de la sombra emitida y las 15 alertas** siguen idénticas.

[Protocolo y resultados detallados](docs/geo2027-log1p-inactive-attenuation-frontier.md) · [Reporte fuente-auditado con 196 países y cinco variantes](data/geo2027-log1p-inactive-attenuation-frontier.json) · [Código reproducible](scripts/experiment_geo2027_log1p_inactive_attenuation_frontier.py) · auditoría independiente con GitHub Actions.

## GEO2027 · Auditoría matemática de sensibilidad de la sombra 2027 ya emitida (16-11-2026)

**Nuevo diagnóstico publicado sobre las 196 probabilidades inmutables de la sombra LOG1P**. Se altera *solo hipotéticamente* el número de muertes UCDP del **origen 2025**, en ±1, ±5 o ±10, **sin cruzar el umbral binario de 25**, sin reentrenar ni el GEO original ni la logística. Se certifican exactamente los extremos de probabilidad mediante monotonicidad de `log1p`/logit, con una segunda prueba de cota analítica basada en el máximo de la derivada logística, y los conjuntos **obligatorios/posibles** de los top-k bajo perturbaciones independientes de todos los países.

| Conteo hipotético 2025 | Anchura media de probabilidad | P95 | Anchura máxima | Top-10 entrada obligatorios | Top-5 salida obligatorios |
|---|---:|---:|---:|---:|---:|
| ±1 muerte | 0,65 pp | 2,09 pp | 4,71 pp | 9/10 | 4/5 |
| ±5 muertes | 2,13 pp | 8,27 pp | 13,32 pp | 2/10 | 3/5 |
| ±10 muertes | 3,18 pp | 11,96 pp | **18,54 pp** | **2/10** | 3/5 |

De los 196 países, **154 registran cero muertes en 2025** y 8 registran entre 1 y 24. El caso de **Burundi**: su probabilidad LOG1P emitida para 2027 es **22,62 %** con cero muertes 2025; con un conteo hipotético 2025 de **10** sin modificar el estado binario subiría a **41,16 %**, +18,54 pp. En ±10, **Chad y Burundi** son los únicos dos miembros garantizados del *top-10 hipotético de entrada* de la sombra. Estos rankings **no** sustituyen las 15 alertas originales.

**Límites:** bandas hipotéticas no probabilísticas, sin estimación de frecuencia de revisiones oficiales, sin reentrenamiento ante una verdadera revisión de años anteriores, sin cruces del umbral ni eventos 2027 observados. **No son intervalos de confianza, de predicción, ni resultados de backtesting.** Las 196 probabilidades originales y sombra, sus SHA, y las 15 alertas previas siguen intactos.

[Protocolo, resultados y certificación](docs/geo2027-log1p-issued-death-count-stress.md) · [Informe completo de los 196 países](data/geo2027-log1p-issued-death-count-stress.json) · Reproductor `scripts/audit_geo2027_log1p_issued_death_stress.py` · Tests `scripts/test_audit_geo2027_log1p_issued_death_stress.py` · Auditoría independiente y gate de publicación GitHub Actions.

## GEO2027 · Robustez a ediciones UCDP del modelo LOG1P (16-11-2026)

**Resultado científico adversarial:** cinco pares de ediciones oficiales UCDP (origen **2022** o **2023** congelado, universo de **196 países**) muestran que la alternativa continua **LOG1P es significativamente más sensible en algunos países** a los cambios de muertes históricas que el modelo Markov binario inicial; esta comparación cuantifica *sensibilidad retrospectiva*, no rendimiento predictivo ni intervalos probabilísticos. Las cinco parejas solapan fuentes y no son réplicas independientes.

| Origen y edición inicial→revisada | Desplazamiento absoluto medio LOG1P | Máximo LOG1P | Markov binario medio |
|---|---:|---:|---:|
| 2022 · 23.1→24.1 | 0,2125 pp | **19,7673 pp** | 0,0469 pp |
| 2022 · 23.1→25.1 | 0,3061 pp | 19,1521 pp | 0,0969 pp |
| 2022 · 23.1→26.1 | 0,3657 pp | 18,2437 pp | 0,1307 pp |
| 2023 · 24.1→25.1 | 0,1756 pp | 5,6727 pp | 0,0610 pp |
| 2023 · 24.1→26.1 | 0,2194 pp | 5,8717 pp | 0,1047 pp |

**Burundi** ilustra el riesgo: en el origen histórico 2022 UCDP cambia **0→10 muertes** (sin alcanzar el umbral binario 25), y LOG1P pasa de **21,18 % a 40,95 %**, diferencia **+19,77 pp**. La descomposición Shapley exacta de tres factores asigna **+19,97 pp** al cambio del conteo del origen, **+0,02 pp** al Markov y **−0,22 pp** al reajuste de coeficientes. En dos parejas 2022 coinciden cambios de pertenencia del **top-10 retrospectivo de entrada (Sudán del Sur→Líbano)** y **top-5 retrospectivo de salida (Indonesia→Tayikistán)**; los demás pares no cambian esas listas.

**Regla no negociable:** ninguna edición anterior a UCDP 26.1 contiene 2025, de modo que estos son **análogos históricos**, no revisiones de la emisión LOG1P real origen 2025→2027. El programa mantiene la primera emisión de la sombra prospectiva, SHA-256 `52686923315854557a796f8f192d376dab77a4e03b14c1aeb6b4091e48104f90`, y las 196 probabilidades GEO originales completamente intactas. Cero resultados oficiales de 2027 resueltos. La mejora retrospectiva de Brier de LOG1P **no prueba robustez editorial ni capacidad predictiva prospectiva**.

Informe con desglose y limitaciones: [robustez vintage LOG1P](docs/geo2027-log1p-historical-vintage-robustness.md), [reporte exacto UCDP](data/geo2027-log1p-historical-vintage-robustness.json); reproducibilidad en `scripts/diagnose_geo2027_log1p_historical_vintage_robustness.py`, pruebas unitarias y GitHub Actions como requisito de despliegue.

## GEO2027 · Nueva emisión sombra prospectiva LOG1P (16-11-2026)

**Se ha emitido una variante nueva y estrictamente separada** del GEO2027 original (196 países) y de la sombra de recalibración existente, para que la señal continua `log(1+muertes)` pueda probarse con resultados de **2027 genuinamente futuros**. El primer commit público del documento íntegro es [`a2af8434`](https://github.com/idealab2026/psicohistoria/commit/a2af84346bd223d2a105cf727b3462cd0955fdac), GitHub **16/11/2026 11:34:38 UTC**; SHA-256 fijo `52686923315854557a796f8f192d376dab77a4e03b14c1aeb6b4091e48104f90`. GitHub no es una notarización temporal independiente.

La fuente sigue siendo UCDP 26.1 **hasta 2025**, sin usar resultados 2026/2027. Se seleccionó ridge **λ=5** con validación interna 2018–2020; el ajuste definitivo utiliza 2012–2025 (2.742 casos históricos). Para el objetivo 2027, las **sumas de probabilidades** de países por encima de 25 muertes estatales son: original **33,6254**, control de intercepto **34,8377**, nueva sombra **35,9840**. Son valores esperados, no resultados observados.

**Contrato ya fijado:** evaluar los tres conjuntos de probabilidades sobre los **mismos 196 países** cuando se publique la **primera edición oficial UCDP completa de 2027**, con diferencia pareada de Brier como métrica principal y log-loss como secundaria. No se imputarán países ausentes como negativos ni se escogerán subgrupos favorablemente después. Los años 2024/2025 habían sido inspeccionados antes de elegir la arquitectura, por lo que **la selección del método no está independientemente validada**, aunque la nueva evaluación de 2027 sea prospectiva. **Cero resultados de 2027 resueltos, cero demostración de habilidad predictiva prospectiva**. Los pronósticos y las 15 alertas originales siguen byte idénticos.

[Protocolo de sombra LOG1P](docs/geo2027-log1p-prospective-shadow-protocol.md) · Archivo [196 probabilidades](data/forecast-2027-log1p-shadow.json) · [Manifiesto inmutable](data/forecast-2027-log1p-shadow-manifest.json) · Generador `scripts/prepare_geo2027_log1p_shadow.py` · auditor SHA `scripts/audit_geo2027_log1p_shadow_issue.py`.

## GEO2027 · Señal continua log1p de intensidad con entrenamiento temporal anidado (16-11-2026)

**Resultado retrospectivo exploratorio (dos años objetivo ya observados en análisis anteriores):** una corrección logística penalizada del **logit de la probabilidad Markov binaria original GEO H2**, utilizando dos pendientes continuas sobre log(1+muertes estatales en el origen), **reduce el Brier agregado de 0,04008406 a 0,03739343** (**−6,7 % relativo**) y el log-loss de **0,15439774 a 0,13868762** (**−10,2 %**). Un control que ajusta *solo* el intercepto alcanza Brier **0,03973310**, de modo que la intensidad aporta mejora incremental frente a la mera recalibración.

Se reconstruyeron dos cohortes de **196 países** y 69 positivos en archivos UCDP originales con SHA-256: 2022→2024 (ediciones 23.1→25.1) y 2023→2025 (24.1→26.1). Cada etiqueta para entrenamiento interno 2012–2017 y selección temporal 2018–2020 se ajusta con un **corte H2 anterior a esa etiqueta**; se eligió λ=5 entre {5,20,80} por validación interna, y los parámetros finales se recalcularon hasta la fecha del origen. La mejora aparece en ambos años, pero en **2025 el grupo originalmente inactivo empeora ligeramente**; 28/196 países muestran deterioro medio.

**Restricción epistémica fundamental:** los resultados 2024/2025 ya habían sido inspeccionados por el laboratorio; aunque no haya fuga de etiquetas posteriores dentro del algoritmo, **no es una validación confirmatoria intocada**. No se adoptará esta variante ni se alterarán pronósticos GEO2027/28 basándose en estos resultados. Ningún resultado futuro certificado de 2027. El resultado negativo del experimento anterior de cuatro estados se conserva íntegro.

Documentación y limitaciones: [protocolo y resultados de intensidad continua](docs/geo2027-log1p-nested-h2.md); [informe completo](data/geo2027-log1p-nested-h2.json); código reproductor `scripts/experiment_geo2027_log1p_nested_h2.py` y pruebas `scripts/test_experiment_geo2027_log1p_nested_h2.py`.

## GEO2027 · ¿Aporta señal predictiva conservar intensidad de muertes? (16-11-2026)

**Resultado negativo de una ablación retrospectiva ex ante con dos ediciones de origen y resultado distintas:** se ha comparado el GEO H2 binario original con una alternativa de **cuatro estados de intensidad de violencia estatal**: 0, 1–24, 25–99 y ≥100 muertes anuales, con el mismo shrinkage local 20, Dirichlet global 1 y horizonte dos años. Las ediciones SHA-fijadas UCDP 23.1→25.1 (2022→2024) y 24.1→26.1 (2023→2025) aportan 196 países por periodo, **392 resultados históricos, 69 positivos**; el código reproduce primero el Brier/logloss exacto del modelo original, bloqueando comparaciones inconsistentes.

| Métrica | Markov binario original | Markov cuatro estados |
|---|---:|---:|
| Brier conjunto (menor es mejor) | **0,04008406** | 0,04244933 |
| Log-loss conjunto | **0,15439774** | 0,15491694 |
| Brier 2024 | **0,04143146** | 0,04627834 |
| Brier 2025 | 0,03873665 | **0,03862031** |

**No hay mejora agregada:** la variante de intensidad empeora el Brier en **aprox. 5,90 %**. A pesar de mejorar el Brier promedio de 163/196 países, los errores mayores en los otros 33 explican el empeoramiento conjunto; los estratos con 1–24 y 25–99 muertes de origen empeoran, mientras que ≥100 mejora. **No se ha reemitido ni cambiado GEO2027, GEO2028 ni sus alertas; cero resultados prospectivos certificados.** Las dos cohortes con años solapados no constituyen una prueba independiente de capacidad predictiva.

Método preregistrado, segmentos y limitaciones: [comparación GEO de intensidad](docs/geo2027-intensity-markov-cross-release.md); [reporte completo de fuentes verificadas](data/geo2027-intensity-markov-cross-release.json). Reproducción: scripts/experiment_geo2027_intensity_markov_cross_release.py; tests: scripts/test_experiment_geo2027_intensity_markov_cross_release.py; GitHub Actions exige coincidencia byte a byte desde las ediciones originales antes de cualquier despliegue.

## GEO2027 · Causa de la revisión histórica de Indonesia (16-11-2026)

**Nuevo resultado reproducido en tres pares oficiales de ediciones UCDP:** para un **origen retrospectivo fijo 2022**, la probabilidad modelizada de Indonesia de estar por encima del umbral de 25 muertes estatales dos pasos después pasó de **65,7575 % (23.1)** a **71,2182 % (26.1)**, +**5,4606 pp**. La atribución Shapley de los conteos de Markov da **+5,4183 pp por revisar la historia de Indonesia** y **+0,0423 pp por revisar las transiciones de los demás países**. En Indonesia, UCDP cambió las etiquetas binarias de **2019 y 2020**, ambas de 0→1; el estado de origen 2022 permanece idéntico. Kirguistán no presenta revisiones nacionales en ese horizonte y cambia +0,2564 pp solo por el ajuste global.

La separación evita contar dos veces el peso de Indonesia en el prior mundial (`global = Indonesia + demás países`). Es **atribución algebraica de datos revisados**, no causalidad, no una nueva predicción 2027 y no una evaluación prospectiva. Ninguna de las 196 probabilidades ni las 15 alertas originales cambia. Cero resultados certificados de 2027.

**Verificación del dato original de mortalidad:** la edición UCDP 23.1 (y 24.1) registra **16 muertes estatales en 2019** y **21 en 2020** para Indonesia; las ediciones 25.1 (y 26.1) registran **34 y 31**, respectivamente. Ambos años cruzan así el umbral binario de 25 muertes, lo que altera varias transiciones anuales del Markov. El desglose de los seis años 2017–2022 y cuatro ediciones, junto a controles SHA-256, está en `data/geo2027-indonesia-raw-death-revisions.json`, con reproductor `scripts/audit_geo2027_indonesia_original_fatalities.py` y pruebas `scripts/test_audit_geo2027_indonesia_original_fatalities.py`. No se atribuye la revisión a incidentes concretos sin sus fuentes de evento.

Fuentes SHA-pinned, tabla de resultados y límites: [informe de atribución](docs/geo2027-indonesia-vintage-revision-attribution.md). Archivo reproducible `data/geo2027-indonesia-vintage-revision-attribution.json`; código `scripts/diagnose_geo2027_indonesia_vintage_attribution.py`; pruebas `scripts/test_diagnose_geo2027_indonesia_vintage_attribution.py`. GitHub Actions exige el resultado byte a byte antes de desplegar.

## GEO2027 · Cambios reales de listas históricas entre ediciones UCDP (16-11-2026)

Estudio retrospectivo reproducible de **seis comparaciones de ediciones oficiales UCDP 23.1–26.1** al **mismo año de origen**, idéntico modelo Markov H2 y presupuestos top-10 de entrada/top-5 de resolución. Entre las seis comparaciones no cambia ningún top-10 de entradas. **Dos pares correlacionados**, ambos con origen 2022 (23.1→25.1 y 23.1→26.1), muestran el **mismo intercambio inequívoco** en el top-5 de resolución: sale Indonesia (GWNO 850) y entra Kirguistán (GWNO 703). Los otros cuatro pares no cambian su top-5; no hubo empates de frontera ni revisión de estado en el origen.

No son seis ensayos independientes ni una actualización de la emisión GEO2027: ninguna de las ediciones antiguas incluye el origen 2025 de las alertas de 2027. Los **196 pronósticos originales**, las **15 alertas emitidas**, el estado sin resultados 2027 y las huellas SHA-256 permanecen intactos. No existe todavía evidencia de habilidad predictiva prospectiva.

Método, resultados país a país y limitaciones: [informe de solapamiento de alertas por edición](docs/geo2027-historical-alert-vintage-overlap.md), reporte numérico `data/geo2027-historical-alert-vintage-overlap.json`, código `scripts/diagnose_geo2027_historical_alert_vintage_overlap.py` y tests `scripts/test_diagnose_geo2027_historical_alert_vintage_overlap.py`. La auditoría de privacidad y los workflows obligan a reconstruir el informe **byte a byte** desde las fuentes oficiales fijadas por SHA-256 antes de desplegar.

## Q-GEO-01 · Evaluador oficial FUTURO de NEWCONF-2027 (11-11-2026)

**Implementado antes de que exista el outcome, sin evaluar ni modificar la emisión original.** Se añade un [contrato de evaluación explícito](docs/newconf-2027-evaluation-contract.md) y el ejecutable `scripts/evaluate_2027_newconf_official.py`. El evaluador toma un CSV **futuro** original de UCDP Intrastate Country Level Multiple Onset con **2027**, URL UCDP HTTPS literal, SHA-256 y fecha posterior a 2027, pero **nunca certifica automáticamente** que el operador haya identificado la primera edición completa.

- Lee y audita **antes de puntuar** el pronóstico de 196 países emitido el 11-11-2026, su hash, generador y manifiesto; no puede modificar ni reentrenar el modelo, la cohorte ni los comparadores.
- Agrega registros de **episodios de conflictos** a `ANY(newconf=1)` por país-año. No utiliza `onset2`, no contabiliza episodios como países y, si falta un registro o una etiqueta en una fila, el país queda **no resuelto**, nunca negativo por defecto.
- Con **menos de 187/196 outcomes resueltos**, informa solo cobertura y casos observados. Entre **187 y 195** permite puntuaciones explícitamente exploratorias, pero no rankings. Con **196** puede medir Brier, log-loss, calibración e **intervalos de top-k** válidos para cualquier desempate de probabilidades.
- La métrica principal permanece congelada: **diferencia Brier modelo − global 2020–24** en la misma cohorte resuelta. Compara adicionalmente país EB, actividad global y referencia sin eventos; intervalo bootstrap de 2.000 remuestreos país.
- Todos los informes se titulan **candidato de resolución** y conservan `first_complete_official_2027_release_independently_attested=false`, `future_predictive_skill_independently_verified=false`; el archivo de fuente por sí solo **no** acredita publicación original, independencia ni superioridad del modelo.
- Se ejecutan pruebas adversariales `scripts/test_evaluate_2027_newconf_official.py` con datos **sintéticos**, como un job `prospective_newconf_2027_resolution_contract` obligatorio para próximos despliegues. **Ningún dato de 2027 se ha observado ni generado en esta implementación.**

El [expediente de futura resolución #45](https://github.com/idealab2026/psicohistoria/issues/45) permanece abierto. La nueva herramienta es un contrato de falsación científica, **no** una mejora del pronóstico inicial ni una evaluación realizada.

## Q-GEO-01 · EMISIÓN PROSPECTIVA REAL NEWCONF-2027 (11-11-2026)

**Estado: EMITIDA, PENDIENTE DE RESULTADOS.** El objetivo es **`ANY(newconf=1)` por país-año** en UCDP *Intrastate Country Level Multiple Onset*, **NO** el `onset2` de *Country Level Onset* ni la violencia anual state-based de 25 muertes ya emitida para GEO-2027.

- **Preregistro formal previo:** [PR #43](https://github.com/idealab2026/psicohistoria/pull/43), incorporada a `main` en el commit **`1ff68f29914124763e29651e956f0086ce0caac4`**, con generador y condiciones en `docs/newconf-2027-protocol.md`. Generador SHA-256 **`353508031023a16f901b61c80d23f6ee83af29e80745a757011881f0dc8c2d14`**.
- **Primera publicación de las 196 probabilidades:** [commit GitHub `f3f2c17c9d4f5dd56266e376cd2d765f33f3dd97`](https://github.com/idealab2026/psicohistoria/commit/f3f2c17c9d4f5dd56266e376cd2d765f33f3dd97), creado el **11-11-2026 10:10:21 UTC**. El documento original `data/forecast-2027-newconf.json` tiene SHA-256 **`e4482da7396872645d5101115435143d98fd9fdb1db1b1fdf41a42c99fc04b74`**, fijado en `data/forecast-2027-newconf-manifest.json`. El estado `PREPARED_FOR_FIRST_PUBLIC_ISSUE` en el propio documento es el valor del generador; la **emisión** queda acreditada por el commit público y manifiesto separado.
- **Cohorte:** 196 países de gobierno con datos en la edición UCDP Multiple Onset 25.1, todos elegibles incluso con conflicto activo. El estado de origen **2025** procede de UCDP/PRIO ACD **26.1**: 32 países con conflicto interno activo, 164 sin él. Se conservan las identidades GW y las cuatro probabilidades **por país**, no solo agregados.
- **Entrenamiento**: `newconf` del histórico 2000–2024 UCDP Multiple Onset 25.1 (SHA `5fe7411942aa7e6a38d6386faa64f4d7f0703482509f121c4136c0e3223d7f05`). Actividad histórica para condicionales de horizonte 2 desde UCDP/PRIO 25.1 (SHA `b49f7e80510d8a5779a52d872aef5b26456b3f5cbdd3ec32031339488e81813f`). El origen 2025 procede exclusivamente de actividad UCDP/PRIO 26.1 (SHA `5f951743222964674a446e32a5a871077b29bd13349588d85fc59953d89c878a`). **No hay** etiquetas `newconf` de 2025, 2026 ni 2027 empleadas.
- **Modelo primario** pre-registrado: tasas país suavizadas hacia tasa global condicionada por actividad intrastatal del origen, regularización 20; horizonte 2025→2027. **Comparador principal**: tasa global de nuevos conflictos en 2020–2024 suavizada por Laplace. La métrica primaria será **Brier(modelo) − Brier(referencia)** con los resultados 2027 efectivamente resueltos.
- **Expectativas agregadas (no resultados):** suma de las 196 probabilidades del modelo = **2,490944756 países-año con `newconf` esperados**, y la referencia global = **1,397148676**. Estos números **no** son la predicción determinista de exactamente dos o tres conflictos y no constituyen conteos observados. La probabilidad modelizada por país oscila de **0,316 % a 10,771 %**, sin ninguna certeza.
- **Evaluación futura:** únicamente desde la primera edición completa y oficial UCDP Multiple Onset que incluya **2027**; los países sin dato quedan **no resueltos**, no negativos. Si se revisan etiquetas, mantener como principal la primera edición y publicar sensibilidad por separado. Rankings con empates de probabilidad en el top-k no son alertas únicas; informar la ambigüedad.
- **Estado científico:** **0 de 196 desenlaces de 2027 resueltos**; ninguna superioridad demostrada. El modelo se especificó después de inspeccionar 2023/2024, de modo que sus resultados históricos son **exploratorios**. No existe notaría temporal independiente, aunque sí un commit público auditable. No se reajusta ninguna probabilidad después de observar un desenlace.
- **Separación rigurosa:** la emisión distinta `PSICO-GEO2027-STATEBASED25-V1` permanece íntegra, SHA `5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5`, con cero resultados evaluados. Ambos objetivos no deben confundirse.

Código de reproducción: `scripts/forecast_2027_newconf.py` (byte exacto, SHA anclado); comprobación independiente `scripts/audit_frozen_newconf_2027.py` y sus pruebas. Registro `data/research.json`, manifiesto `data/forecast-2027-newconf-manifest.json`, resumen `data/forecast-2027-newconf-audit.json`. Ambos se muestran en **Predicciones → Riesgos 2027** e **Investigación → Evidencia**. El CI del despliegue reconstruye el documento desde los tres originales y compara sus bytes con la primera emisión.

## Q-GEO-01 · Conflictos nuevos en países con actividad: `newconf` versus `onset2` (11-11-2026)

**Nuevo objetivo de investigación separado de Country Level Onset:** UCDP distingue tres variantes de inicio de conflicto. El [manual de UCDP Onset 25.1](https://ucdp.uu.se/downloads/onset/ucdp-codebook-onset-251.pdf) define *Intrastate Country Level Onset* (versión 2) y *Intrastate Country Level Multiple Onset* (versión 3). El primero no admite un `onset2` mientras otro conflicto interno está activo en el país. El segundo admite episodios de **conflictos nuevos** en países que ya tienen otros activos; su columna `newconf` **no equivale** a `onset2`, pues esta última exige un determinado período de inactividad antes del reinicio.

Se han descargado del **[índice oficial de versiones históricas de UCDP](https://ucdp.uu.se/downloads/olddw.html)** los dos CSV correspondientes a la versión 3:

- **UCDP Country Multiple Onset 23.1**, `https://ucdp.uu.se/downloads/onset/ucdp-intrastate-country-multiple-onset-231.csv`, SHA-256 `a31abf6c278bd3a14d6c5b64e075cb38cebe63c95e0535454426c09be21d60e3`: **12.212 filas de episodios**, pero **12.161 países-año únicos**, con 39 claves país-año repetidas.
- **UCDP Country Multiple Onset 25.1**, `https://ucdp.uu.se/downloads/onset/ucdp-intrastate-country-multiple-onset-251.csv`, SHA-256 `5fe7411942aa7e6a38d6386faa64f4d7f0703482509f121c4136c0e3223d7f05`: **12.606 filas de episodios**, pero **12.553 países-año únicos**, con 41 claves repetidas.

**Regla de integridad:** repetir un país-año en este archivo es legítimo: pueden existir varios episodios de conflictos distintos dentro del mismo país y año. Se preserva el número de episodios por separado y, al evaluar el riesgo por país-año, se agrega **`ANY(newconf=1)`**. Jamás se cuentan las 12.606 filas como 12.606 países-año independientes.

### Dos resultados diferentes en el mismo año

| Indicador en la versión Multiple Onset 25.1 | 2023 | 2024 |
|---|---:|---:|
| Países-año con `newconf=1` | **2** | **1** |
| Países-año con `onset2=1` | 1 | 1 |
| Países-año con `newconf=1` y `onset2=0` | **2** | **1** |

Se ha elaborado un **nuevo estimador de `newconf`**, separado del modelo de `onset2`, con fuentes congeladas y límites temporales: edición 23.1 exclusivamente para modelos e incidencia de conflicto interno (UCDP/PRIO 23.1), y etiquetas de la edición 25.1 solo para resolver 2023–2024. El origen de emisión simulado es **2022 para ambos años**; para 2024 no se utiliza ningún dato de 2023 como predictor. La variante Multiple Onset admite países con conflicto activo como **elegibles**.

| Modelo | Brier rolling histórico ↓ | Brier externo 2023–24 ↓ | Log-loss externo ↓ |
|---|---:|---:|---:|
| Global, últimos cinco años | 0,01778590 | 0,00760089 | 0,04526181 |
| Global, histórico completo | 0,01762152 | 0,00762242 | 0,04619501 |
| País, regularización EB | 0,01756741 | 0,00722145 | 0,03572861 |
| Actividad interna en origen, global | **0,01736473** | 0,00734596 | 0,03699072 |
| **País + actividad interna en origen** | 0,01752334 | **0,00715411** | **0,03377868** |
| Sin nuevos conflictos (referencia Brier) | 0,01785714 | 0,00765306 | No definido con positivos |

**Validación interna:** 2.744 evaluaciones de pronósticos solapados, **1.568 país-año distintos y 33 etiquetas `newconf` positivas únicas**. Los 49 positivos registrados por pronóstico incluyen desenlaces repetidos entre horizontes. El estimador más favorable en el histórico interno por Brier es *actividad global*, mientras que el más favorable en el contraste externo es *país + actividad interna*; **no se selecciona ninguno como modelo ganador prospectivo**.

**Contraste externo:** **392 países-año y solo tres positivos** de `newconf` en 2023/2024: dos en 2023 y uno en 2024. **Los tres tenían conflictos internos activos en 2022** (34 países activos frente a 162 sin esa actividad). El modelo país+actividad obtiene menor Brier que la tasa global reciente, pero su intervalo descriptivo de diferencia por bootstrap país **[−0,00152703, +0,00036351] cruza cero**. Además, la lista top-20 presenta **empates en su frontera ambos años**: los 2/20 y 1/20 casos contados dependen del desempate por identificador, por lo que no constituyen tres alertas inequívocas ni una demostración de capacidad de ranking operativo.

**Límites científicos:** todos los modelos y el cambio de objetivo se desarrollaron **después de inspeccionar 2023 y 2024**. Por tanto, este estudio es *post hoc*, no test independiente ni prospectivo. Hay solo **tres** positivos externos y ni siquiera el bootstrap por país captura shocks internacionales compartidos. `newconf` indica conflictos nuevos codificados por UCDP, no todos los cambios de violencia ni la totalidad de guerras simultáneas. La procedencia de cada archivo está identificada mediante SHA-256; la fecha original de disponibilidad pública de las ediciones históricas no está independientemente certificada.

**Código y publicaciones:** `scripts/probe_multiple_onset_vintages.py`, `scripts/experiment_multiple_newconf.py` y sus pruebas adversariales; fuentes y diferencias agregadas en `data/country-multiple-onset-source-audit.json`, estimaciones completas en `data/country-multiple-newconf-experiment.json`, contratos `src/research.mjs`, web **Investigación → Evidencia**, y jobs obligatorios de CI para futuros despliegues. El experimento no modifica ninguna de las **196 probabilidades originalmente emitidas para GEO-2027**, ni atribuye resultados a 2027.

## Q-GEO-01 · Corrección del conjunto en riesgo oficial de onset2 (10-11-2026)

**Corrección sustantiva tras verificar el [manual UCDP Onset 25.1](https://ucdp.uu.se/downloads/onset/ucdp-codebook-onset-251.pdf):** nuestra variable dependiente procede de **UCDP Intrastate Country Level Onset, versión 2**. Su unidad es **país-año**. En esta variante *no se registra un inicio de conflicto interno si ya continúa otro conflicto intrastatal en el país*. Esto contradice la afirmación anterior de que podía contarse un onset de otro conflicto simultáneo. Esa propiedad pertenece a la variante distinta **UCDP Intrastate Country Level Multiple Onset, versión 3**, o al dataset específico por conflicto. Los tres productos **no son intercambiables**.

Para `onset2`, el país debe llevar al menos **dos años completos sin actividad intrastatal** antes del objetivo T. El conjunto de riesgo operativo depende de la información disponible al emitir, nunca de resultados posteriores:
- **Horizonte 1 año**, corte 2022 → objetivo 2023: actividad de 2021 y 2022 ya conocida; **160 países elegibles conocidos**, **36 inelegibles conocidos**, universo de 196. El único `onset2` observado estaba en el conjunto elegible.
- **Horizonte 2 años**, corte 2022 → objetivo 2024: la actividad de 2023 todavía no estaba disponible; **34 países eran inelegibles conocidos** por actividad en 2022 y los **162 restantes son candidatos con elegibilidad pendiente de 2023**, **no 162 elegibles verificados**. El único `onset2` de 2024 está entre esos 162.
- Un análisis realizado *ex post* con la edición posterior 25.1 identifica **159 países elegibles** al revisar 2023 y **159** al revisar 2024; son **descripciones a posteriori**. No pueden usarse para filtrar retrospectivamente el conjunto de pronósticos emitidos desde 2022.
- La auditoría de los **14 cortes históricos** de 23.1 no encuentra eventos `onset2` positivos dentro de países sabidamente inelegibles en el origen. Ambas comparaciones 2023/2024 tienen cero discrepancias de este tipo entre ediciones.

**Consecuencia metodológica:** los Brier, AP y rankings publicados en los estudios anteriores se calcularon sobre los **196 países sin un filtrado por el conjunto en riesgo**. Se conservan como evidencia de su estimando original; **NO deben interpretarse como validación predictiva condicional entre los elegibles**. No se recorta la cohorte con etiquetas futuras ni se retocan las probabilidades ya emitidas de GEO-2027, que además predice **otra variable** (violencia estatal-organizada).

**Código y evidencias:** `scripts/audit_onset2_country_riskset.py`, `scripts/test_audit_onset2_country_riskset.py`, `data/onset2-country-riskset-audit.json`. El estudio descarga cuatro archivos UCDP oficiales SHA-256: Onset y UCDP/PRIO 23.1 (corte) y 25.1 (auditoría posterior), separa hechos conocidos de estados contingentes y conserva solo agregados. Los resultados se reproducen exactamente en un nuevo job de GitHub Actions **obligatorio antes del despliegue**. La web Investigación → Evidencia muestra el cambio con un enlace al código oficial. No se afirma nueva habilidad predictiva ni emisiones históricas.

## Q-GEO-01 · Incidencia real de conflictos internos UCDP/PRIO (10-11-2026)

**Nueva fuente oficial, nuevo experimento y resultado no confirmatorio:** hemos incorporado el [UCDP/PRIO Armed Conflict Dataset, ediciones históricas 23.1 y 25.1](https://ucdp.uu.se/downloads/olddw.html) para conocer la **presencia de conflicto interno activo en un país y año**, en vez de depender únicamente de la señal puntual `onset1`. El código comprueba que el UCDP/PRIO es una fuente **conflicto-año**, filtra únicamente los tipos 3 (*intrastate*) y 4 (*internationalized intrastate*), y agrega por el código Gleditsch-Ward `gwno_a` del gobierno primario. **Nunca** se une directamente un registro conflicto-año con una etiqueta `onset2` país-año sin esta transformación. Los conflictos de tipo 1 y 2 se excluyen del predictor.

**Fuentes originales ancladas por SHA-256**:
- UCDP/PRIO Armed Conflict Dataset **23.1**, ZIP CSV con **2.626 filas conflicto-año**, 2.368 internas/internacionalizadas, **1.711 país-año activos** hasta 2022 y **34 países** con conflicto interno activo en 2022. SHA-256 `8fe95d8a5780cba1d312f9673ffd9e93b90c91bb26e348393a583853a892b718`.
- UCDP/PRIO Armed Conflict Dataset **25.1**, ZIP CSV con **2.752 filas conflicto-año**, 2.488 internas/internacionalizadas, **1.780 país-año activos** hasta 2024 y **33 países** con actividad en 2024. SHA-256 `b49f7e80510d8a5779a52d872aef5b26456b3f5cbdd3ec32031339488e81813f`.
- UCDP Intrastate Country Onset **23.1** (para todo el entrenamiento, SHA-256 `e2cadfa7a87b3949f8c638c27381fbb1b44fb076ccb00570782252d0935a2289`) y **25.1** (solo resultados 2023–2024, SHA-256 `e2b59e65aaca88403991465b78fb407d7eddcefadeb18c7f1397bfe2ea83fe6a`).

La unión automática no detectó códigos gubernamentales multivaluados ni incompatibles en los conflictos internos, y todos los códigos de país utilizados están representados en el archivo `onset2`. Entre las dos ediciones de actividad, el histórico común hasta 2022 registra **5 país-año añadidos y 2 eliminados** por revisiones; **ningún valor revisado de 25.1 entra en la estimación**.

### Comparación reproducible

Se evalúan siete referencias/variantes predefinidas, incluyendo dos nuevas señales de conflictos armados: actividad interna en el origen y cualquier actividad en los últimos tres años del origen, con regularización empírico-bayesiana de fuerza 20. Los cortes internos 2014–2020 y el origen externo 2022 emplean **solo información existente hasta cada corte** en ambas fuentes de 23.1. Para evaluar el año 2024, el modelo **no lee ni utiliza la situación de 2023**.

| Especificación | Brier rolling interno ↓ | Brier externo 2023–24 ↓ |
|---|---:|---:|
| Tasa global últimos cinco años | 0,01332696 | **0,00514221** |
| Tasa global completa, por horizonte | 0,01331910 | 0,00519987 |
| País EB sin conflictos activos | 0,01332146 | 0,00543315 |
| País + marcador anterior `onset1` | 0,01330592 | 0,00542598 |
| Actividad interna en origen, tasa condicionada global | 0,01327676 | 0,00520147 |
| **País + actividad interna en origen** | **0,01321659** | **0,00536699** |
| País + actividad en últimos 3 años | 0,01332036 | 0,00547462 |

El nuevo predictor mejora modestamente el Brier del estimador país EB en el rolling (**0,79 %**) y en la prueba externa (**1,22 %**). El intervalo por bootstrap agrupado en países para la diferencia externa Brier modelo actividad-país menos EB es **[−0,00010153, −0,00003292]**, pero **no supera** la referencia más competitiva, tasa global reciente (Brier 0,00514221); su intervalo frente a esta es **[−0,00000891, +0,00043796]**, cruza cero. Con solo **dos inicios externos**, dichos intervalos son exploratorios y no capturan shocks globales ni multiplicidad de modelos.

El rolling interno contiene **2.744 evaluaciones**, pero solo **1.568 país-año distintos y 22 inicios únicos** por solapamiento de orígenes/horizontes. En la validación 2023–24 hay **392 evaluaciones y 2 eventos**. Los **dos `onset2` positivos se dan en países sin conflicto interno activo en 2022**. El modelo país+actividad identifica **0 de los 2 eventos en los top-20** de cada año. La variable aporta información descriptiva sobre incidencia, pero **no demuestra anticipación útil del inicio de guerras**.

**Limitaciones y transparencia:** hipótesis seleccionadas después de haber inspeccionado resultados 2023/24, estudio ex post realizado en 2026; no es evaluación independiente ni se conocen fechas originales de acceso notarizadas. UCDP/PRIO y el indicador `onset2` tienen unidades y semántica distintas. La presencia de un conflicto activo puede coexistir con el inicio de otro conflicto, pero **el indicador Country Level Onset utilizado aquí NO codifica ese nuevo inicio como `onset2`**. Para contabilizar nuevos conflictos durante otros conflictos activos hay que cambiar a la variante **Country Level Multiple Onset** o por conflicto. La serie del mismo archivo revisado tampoco constituye backtest histórico point-in-time. En ningún caso se modifican las **196 probabilidades ya emitidas de GEO-2027** ni se acreditan resultados de 2027.

**Archivos:** `scripts/probe_ucdp_prio_incidence.py`, `scripts/experiment_onset2_conflict_incidence.py` y sus tests adversariales; informe de fuentes `data/ucdp-prio-incidence-vintages.json`, resultados `data/onset2-conflict-incidence-ablation.json`, registro científico `data/research.json`, vista **Investigación → Evidencia** y dos nuevas condiciones obligatorias en CI antes de publicar.

## Q-GEO-01 · Prueba de información adicional: `onset1` previo y horizonte estrictamente congelado (10-11-2026)

**Nueva investigación reproducida, resultado externo desfavorable:** hemos contrastado cinco especificaciones para predecir `onset2` de UCDP utilizando únicamente el indicador `onset1` **del último año disponible en la edición de origen**, sin leer nunca datos del año objetivo ni del año intermedio. Los modelos tienen parámetros fijos, Beta-Laplace(1,1) para tasas, shrinkage=20 para país/grupo, y dos horizontes separados de **1 y 2 pasos anuales**. No se han calibrado ni seleccionado modelos mediante los resultados externos.

La edición **UCDP Intrastate Country-Level Onset 23.1** (SHA-256 `e2cadfa7a87b3949f8c638c27381fbb1b44fb076ccb00570782252d0935a2289`) aporta la historia de `onset1`/`onset2` y toda la estimación. Los resultados de 2023–2024 proceden exclusivamente de **25.1** (SHA-256 `e2b59e65aaca88403991465b78fb407d7eddcefadeb18c7f1397bfe2ea83fe6a`). Una validación interna aplica cortes anuales 2014–2020 dentro de 23.1, cada uno con horizontes 1 y 2. La revisión de esos datos históricos en la edición de 2023 impide llamarlos históricos *as-of* auténticos.

| Especificación | Brier interno 2015–2022 ↓ | Brier externo 2023–2024 ↓ |
|---|---:|---:|
| Global · últimos 5 años | 0,01332696 | **0,00514221** |
| Global · tasa según horizonte | 0,01331910 | 0,00519987 |
| País · tasa Empirical Bayes | 0,01332146 | 0,00543315 |
| Señal `onset1` del origen, tasa condicionada | 0,01331239 | 0,00519769 |
| País + señal `onset1` | **0,01330592** | 0,00542598 |

**Validación interna:** **2.744 evaluaciones país–origen–horizonte**, pero solo **1.568 país-año distintos y 22 inicios únicos**: los 37 positivos contabilizados por pronóstico incluyen desenlaces repetidos desde distintos orígenes. Por horizonte hay 1.372 evaluaciones (19 positivos a un año, 18 a dos años). Es una muestra de predicciones temporalmente solapadas, **no 2.744 observaciones independientes**. La señal adicional mejora ligeramente el Brier frente a la tasa solo por país. **Contraste externo:** 392 países-año con **solo dos eventos**; ninguna especificación por país supera a la tasa global de los últimos cinco años. El delta Brier externo del modelo con señal frente al modelo solo por país tiene intervalo exploratorio **[−0,0000170, +0,0000002]**, incluye cero; frente a la tasa global-h también es peor. En los dos años el top-20 del modelo con señal encuentra **cero de dos eventos**. Los indicadores de ranking tienen enorme incertidumbre por la escasez de positivos.

**Qué aprende realmente:** `onset1` marca un inicio de conflicto pasado, pero **no contiene el estado completo de actividad bélica ni determina el conjunto de países en riesgo** de `onset2` de acuerdo con la definición oficial. El siguiente experimento útil deberá incorporar *incidencia de conflicto* y factores explicativos exógenos, verificando cuidadosamente las series y fechas de disponibilidad. Añadir variantes del propio historial `onset2` sin esa información no es un sustituto satisfactorio.

**Limitación metodológica:** las cinco variantes se diseñaron después de observar el contraste 2023–2024 en investigaciones anteriores. Este estudio es post hoc y **no permite afirmar mejora confirmatoria**. Los bootstraps por país no capturan choques globales compartidos; la validación interna comparte edición revisada. No se emiten nuevas predicciones prospectivas ni se modifica la emisión GEO-2027 de **196 probabilidades**.

Código y reporte: `scripts/experiment_onset2_lagged_signals.py`, `scripts/test_experiment_onset2_lagged_signals.py` y `data/onset2-lagged-origin-ablation.json`. Se registran los 14 cortes internos, los dos cortes externos, pérdidas, ordenaciones e intervalos; un job CI obligatorio recalcula todos los datos desde los dos archivos oficiales verificados por SHA-256.

## Q-GEO-01 · Inicio real de conflictos (`onset2`), separado de persistencia (10-11-2026)

**Nuevo resultado negativo con unidad homogénea:** hemos utilizado exclusivamente ediciones originales **UCDP Intrastate Country Level Onset 23.1 y 25.1**, con URL y SHA-256 comprobados, sin mezclar el archivo 19.1 que tiene 47 país-año duplicados y posibles divergencias de unidad. La edición 23.1 proporciona entrenamiento 2000–2022 y 25.1 resultados de los años 2023 y 2024. La edición 23.1 no estuvo disponible al inicio de 2022: los cortes anuales no equivalen a años completos de preaviso operativo.

**392 país-año, dos positivos `onset2`** (uno en 2023 y otro en 2024). El resultado mide *inicio/reinicio* de conflicto armado según UCDP; es radicalmente distinto de la variable binaria de 25 muertes por violencia organizada de base estatal del modelo GEO-2027.

| Estimador | Brier ↓ | Log-loss ↓ |
|---|---:|---:|
| Tasa empírica por país, regularización 20 | 0,00543370 | 0,03769405 |
| Tasa global histórica | 0,00520104 | 0,03734212 |
| Tasa global 2018–2022 | 0,00514221 | **0,03532320** |
| Pronosticar ausencia de inicios | **0,00510204** | No definido para eventos positivos |

El estimador por país pierde en Brier frente a todas las referencias; su skill relativo al global es **−4,47 %**. El contraste es desfavorable incluso sin utilizar el problemático archivo 19.1. Intervalo exploratorio de diferencia Brier modelo − global, bootstrap por país 2000 réplicas: **[+0,0000081,+0,0004637]**; los shocks compartidos entre países no están representados y solo hay dos eventos.

**Ordenación muy limitada:** 2023 tiene un solo positivo, average precision **0,51 %**, ROC-AUC **0,359**; 2024 tiene uno, average precision **1,92 %**, ROC-AUC **0,826**. En ninguno de los dos años el evento aparece entre los **20 primeros países** del modelo. No basta para demostrar que ningún modelo sea capaz de anticipar guerras; sí refuta que el estimador ensayado ya ofrezca utilidad validada.

**Revisiones históricas:** al comparar 23.1 y 25.1, las ediciones comparten 12.161 país-año hasta 2022, con **dos cambios `onset2`** (2018: 0→1; 2021: 1→0), reportados por separado. No se utilizaron las revisiones de 25.1 al ajustar el estimador.

Todos los resultados se reproducen en `scripts/evaluate_homogeneous_onset2.py` y `data/onset2-231-251-homogeneous.json`; pruebas `scripts/test_evaluate_homogeneous_onset2.py`, auditoría de privacidad, contrato de integridad `src/research.mjs` y vista **Investigación → Evidencia**. Se fuerza un nuevo job de verificación de UCDP Onset antes de desplegar la web.

**Alcance:** reconstrucción retrospectiva efectuada en 2026, sin emisiones prospectivas anteriores, sin fechas independientemente notariadas y con solo dos casos positivos. **No modifica las 196 probabilidades de GEO-2027 ni resuelve resultados de 2027.**

## GEO-2027 · Nuevo contraste sobre entradas, calibración y ranking (10-11-2026)

El modelo GEO-2027 había reducido el Brier agregado principalmente por **persistencia de estados violentos**. Para no confundir eso con detección de nuevas entradas, se ha ejecutado otro análisis —**exploratorio y especificado después de observar los resultados históricos**— solo sobre los países que estaban por debajo del umbral de 25 muertes por violencia organizada *state-based* en los años origen 2022 y 2023.

**Universo**: 321 países-año inicialmente inferiores al umbral; solo **8** lo superan en 2024/2025 (4 por año). Ediciones UCDP **23.1→25.1** y **24.1→26.1**, cada archivo comprobado mediante SHA-256. El modelo por país es exactamente el previamente emitido; no se retoca ninguna de las 196 probabilidades de 2027.

Nueva referencia *no usada para entrenar el modelo*: tasa histórica de entrada a los dos años de países inicialmente inactivos, con suavizado Beta(1,1), utilizando únicamente el archivo original anterior al año objetivo. Para origen 2022 hay **5.175** observaciones históricas elegibles, **199** entradas y tasa predictiva **3,8632 %**; para origen 2023, **5.339** observaciones, **205** entradas y tasa **3,8570 %**. El último año histórico usado en cada referencia acaba dos años antes del corte de origen, para permitir observar las transiciones sin fuga de datos.

| Modelo | Brier ↓ | Log-loss ↓ |
|---|---:|---:|
| Markov por país, sin modificar | **0,02264753** | **0,10025935** |
| Tasa histórica directa de entrada a 2 años | 0,02448810 | 0,11949285 |
| Markov global, desde estado inactivo | 0,02521028 | 0,12748894 |

La mejora retrospectiva Brier es **7,52 %** frente a la referencia directa y **10,17 %** frente al Markov global. El intervalo exploratorio de diferencia Brier frente a la referencia directa **[−0,00728, +0,00175] incluye cero**; no prueba una superioridad robusta con solo ocho positivos.

**Calibración**: el modelo asignó una probabilidad media de **4,2056 %** frente al **2,4922 %** observado: pronosticó **1,6875 veces** más entradas esperadas que las ocurridas. No basta con un Brier relativamente favorable para decir que está bien calibrado.

**Ordenación de alertas** (solo entre países inicialmente inferiores al umbral): para 2024 la *average precision* (AP/PR-AUC discreta) fue **25,42 %**, ROC-AUC **0,9226**, y el top-5 detectó **2 de 4** entradas; para 2025, AP **18,09 %**, ROC-AUC **0,8149**, top-5 detectó **1 de 4**. La tasa base de un clasificador sin capacidad de ordenación ronda **2,5 %**. Solo dos años objetivo: los resultados están muy expuestos al azar y no deben extrapolarse a otros periodos sin evaluación independiente.

**No es predicción del inicio de guerras**: cruzar el umbral de 25 fallecimientos state-based no equivale a `onset2` y tampoco mide violencia gubernamental contra civiles. Las fuentes históricas se recuperaron y los modelos se reconstruyeron ex post en 2026; las fechas originales de emisión no están autenticadas de forma independiente. Ni estos datos ni las nuevas referencias validan prospectivamente el modelo. **En 2027 siguen pendientes los 196 desenlaces y no se ha alterado ninguna probabilidad emitida**.

Reproducibilidad: `scripts/evaluate_2027_new_entries.py`, tests `scripts/test_evaluate_2027_new_entries.py`, informe `data/forecast-2027-entry-comparison.json`, resumen estricto en `data/research.json` y vista **Investigación → Evidencia**. Los análisis emplean solo ficheros oficiales anclados por SHA y se recalculan en CI, que impide desplegar si el informe cambia.

## GEO-2027 · Persistencia frente a nuevos cruces de umbral (10-11-2026)

**La mejora agregada no responde necesariamente a predecir nuevas guerras.** Hemos descompuesto las 392 observaciones históricas de ediciones UCDP distintas según el estado del país al final del año de origen, utilizando **exactamente el modelo Markov emitido para 2027**, sin modificar las probabilidades públicas.

| Estado en el año de origen | Países-año | Resultados positivos en el año evaluado | Brier modelo | Brier Markov global | Brier Skill |
|---|---:|---:|---:|---:|---:|
| Ya superaban 25 muertes `state-based` | **71** | **61** | 0,11892 | 0,14508 | **+18,03 %** |
| Estaban por debajo del umbral | **321** | **8** | 0,02265 | 0,02521 | **+10,17 %** |

**61 de 69 positivos (88,41 %) corresponden a persistencia de una situación ya por encima del umbral.** Solo ocho positivos partían de un estado anterior por debajo de 25. El intervalo de bootstrap agrupado por país para la diferencia Brier (modelo menos Markov global) en el estrato inicialmente inferior a 25 es **[−0,00740, +0,00068]**, **incluye cero**; no acredita una mejora sólida para nuevos cruces del umbral. Para países ya por encima del umbral el intervalo exploratorio es **[−0,03965, −0,01220]**. Dos años objetivo no permiten modelar adecuadamente choques compartidos entre países.

Por año, 2024 registra 4 entradas al estado positivo y 31 persistencias, frente a 2025 con otras 4 entradas y 30 persistencias. La precisión retrospectiva top-10 (10/10 en 2024 y 9/10 en 2025) está dominada por continuidad de conflictos violentos existentes, **no demuestra detección del inicio de nuevas guerras**. La variable es *muertes por violencia organizada con participación estatal*, no el indicador UCDP `onset2`.

**Otra restricción temporal:** el horizonte Markov es de **dos pasos entre años de datos** (2022→2024; 2023→2025); las ediciones que contienen el estado del año de origen solo se publican después del cierre de ese año. Por tanto, no cabe afirmar que esos resultados habrían estado disponibles con **dos años completos de preaviso operativo**. Las fechas de publicación originales carecen de notarización independiente y el experimento se reconstruyó en 2026.

El estudio se ejecuta con los cuatro archivos UCDP protegidos por hash y se publica en `data/forecast-2027-origin-state-diagnostic.json`; código `scripts/diagnose_2027_origin_state.py`, tests adversariales y control obligatorio `origin_state_diagnostic` antes de despliegue. **No se han emitido nuevas predicciones ni evaluado resultados de 2027.** La cohorte prospectiva original de 196 países conserva sus probabilidades y su SHA-256.

## GEO-2027 · Contraste histórico entre ediciones oficiales realmente distintas (10-11-2026)

**Resultado nuevo:** investigación con la misma ecuación probabilística, horizonte de dos años y referencias previamente congelados para GEO-2027, pero esta vez los años de entrenamiento proceden de una edición UCDP previa **diferente** de la utilizada para observar cada desenlace. No se reconstruye el pasado únicamente con una misma edición revisada.

| Ficheros de origen → resultado | Corte de entrenamiento | Año observado | Países | Umbral superado |
|---|---:|---:|---:|---:|
| OrganizedViolenceCY **23.1 → 25.1** | 2022 | 2024 | 196 | 35 |
| OrganizedViolenceCY **24.1 → 26.1** | 2023 | 2025 | 196 | 34 |
| **Total** | | | **392** | **69** |

La versión 23.1 original existe como **Excel XLSX**, mientras 24.1/25.1/26.1 se descargan en CSV comprimido; se procesan por separado con validación estricta de la unidad país-año y las columnas oficiales `country_id_cy`, `year_cy`, `sb_total_deaths_best_cy` (alias sin sufijo en 26.1). El motor verifica SHA-256 **antes** de cargar cada archivo, prohíbe cualquier observación posterior al corte dentro del entrenamiento y solo añade el resultado del año objetivo a la evaluación.

| Modelo | Brier ↓ | Log-loss ↓ |
|---|---:|---:|
| Markov por país, prior 20 | **0,04008406** | **0,15439774** |
| Markov global | 0,04692112 | 0,19006909 |
| Frecuencia global últimos cinco años | 0,14506787 | 0,46541257 |

Mejora retrospectiva en Brier: **14,57 % frente a Markov global** y **72,37 % frente a frecuencia global**. La calibración descriptiva por siete bandas presenta un error absoluto agrupado de **3,46 puntos porcentuales**; algunas bandas tienen muy pocos casos y no permiten inferencia prospectiva. El bootstrap exploratorio agrupado en país (2000 réplicas) arroja una diferencia modelo menos Markov global entre **−0,01133 y −0,00287**. No captura adecuadamente los choques compartidos ni el escaso número de años objetivo.

La revisión histórica de etiquetas binarias aporta un control empírico: **6 cambios** entre las ediciones 23.1→25.1 en 6544 países-año comunes hasta 2022; **7 cambios** entre 24.1→26.1 en 6740 registros hasta 2023. El entrenamiento se basa estrictamente en la versión antigua, sin utilizar esas revisiones posteriores.

**Ficheros fuente oficiales y sus huellas**: 23.1 XLSX `6c7dc09cc3173b21568a88d70862bee6a9199b2c6b217719698d9298ca8ecaff`; 24.1 ZIP `00410bdb65023d1bc8799f47f188677965046bb73447ee33094782db30076260`; 25.1 ZIP `564ce9a33652a5d7adef30f00ce6ac86411dedbcc10ef60ca9bdfbfeb9fea917`; 26.1 ZIP `66910888f5653af42776d2debc1d72fe527559e7f7fc82e69b7c8771467f2d34`. Los enlaces se descubrieron en el [archivo histórico oficial](https://ucdp.uu.se/downloads/olddw.html), no se infirieron.

**Límite irrenunciable:** el estudio se ha ejecutado **ex post en 2026**. Aunque la estructura y el contenido de las ediciones archivadas se verifican, **las fechas originales no tienen un sellado independiente y no se emitió realmente ninguna predicción en 2023–2024**. El nuevo contraste es mejor evidencia histórica que la prueba de vintage revisada, pero todavía no equivale a la validación prospectiva de 2027.

Resultados reproducibles en `data/forecast-2027-archival-cross-release.json`; código `scripts/backtest_archived_country_vintages.py` y pruebas `scripts/test_backtest_archived_country_vintages.py`. GitHub Actions recalcula el resultado desde los cuatro archivos oficiales con hash fijado y bloquea el despliegue si cambia. **Las 196 probabilidades de 2027, su SHA y su protocolo no cambian; cero resultados de 2027 evaluados.**

## GEO-2027 · Backtest retrospectivo del modelo emitido (10-11-2026)

Se ha evaluado **exactamente el modelo y los baselines fijados para GEO-2027**, sin alterar el JSON de 196 pronósticos ni sus parámetros: Markov por país con prior 20, Laplace 1 y horizonte de dos años; referencias Markov global y frecuencia global de los cinco años anteriores al origen.

El motor `scripts/backtest_statebased_2027_spec.py` genera un *rolling-origin* de **14 años objetivo, 2012–2025**, fijando el entrenamiento en cada año objetivo menos dos. La fuente es la única edición oficial UCDP OrganizedViolenceCY 26.1 (SHA-256 **`66910888f5653af42776d2debc1d72fe527559e7f7fc82e69b7c8771467f2d34`**), por lo que su **historial está revisado retrospectivamente en 2026**: no es un estudio *point-in-time* verificado ni evidencia de predicciones emitidas antes de cada año.

| Modelo | Brier (menor es mejor) | Log-loss (menor es mejor) |
|---|---:|---:|
| Markov por país (idéntica fórmula a GEO-2027) | **0,04502180** | **0,17294718** |
| Markov global | 0,05151912 | 0,20554572 |
| Frecuencia global de los últimos cinco años | 0,13828517 | 0,44938370 |

Resultados: **2.742** observaciones país-año, **454** observaciones que superaron el umbral de 25 fallecimientos; **12,61 %** de reducción relativa de Brier respecto al Markov global y **67,44 %** respecto a la frecuencia global. El contraste por bootstrap agrupado en país (2.000 réplicas) da un intervalo exploratorio para la diferencia Brier modelo menos Markov global de **[−0,00932, −0,00379]**. La agrupación por país no captura choques comunes entre países ni toda la dependencia derivada de horizontes solapados; no se utiliza para reclamar significación confirmatoria. El error absoluto de calibración por los grupos fijados es aproximadamente **3,20 pp** (modelo) y **4,81 pp** (Markov global), dependiente de los intervalos de agrupación.

El estudio completo incluye los 14 años individuales, intervalos, probabilidades medias frente a tasas observadas, ausencia de etiquetas interpretadas como cero y pruebas contra fuga de información posterior al origen. Archivo agregado `data/forecast-2027-historical-backtest.json`, resumen en `data/research.json`, tests en `scripts/test_backtest_statebased_2027_spec.py`. **No hay datos de resultado de 2027 y no se modifican las 196 predicciones publicadas**. La evaluación verdaderamente prospectiva sigue pendiente de la primera edición oficial completa posterior a 2027.

## GEO-2027 · Auditoría independiente de reproducibilidad (10-11-2026)

Un segundo cálculo independiente ha reconstruido **las 196 probabilidades originales** utilizando únicamente el ZIP oficial **UCDP OrganizedViolenceCY 26.1** con SHA-256 fijo. El job ejecuta dos comprobaciones complementarias: (i) regenera el fichero de emisión **byte por byte** con el código preregistrado, y (ii) implementa las ecuaciones Markov de forma separada y compara cada probabilidad por país con la ya publicada. El fichero original no se reescribe.

Resultados agregados registrados en `data/forecast-2027-audit.json`: 34 países superaban el umbral en 2025; para 2027 la suma de probabilidades del modelo es **33,6254** países y la suma de la referencia global es **34,5295**. Existen 73 valores de probabilidad diferentes entre 196 países; 112 están por debajo del 5 % y 34 por encima del 50 %. Se trata de **distribuciones previstas, no resultados futuros observados**. Ningún pronóstico ha sido evaluado ni se reclama superioridad del modelo.

La auditoría se ejecuta en CI con `scripts/audit_frozen_2027.py --check-report data/forecast-2027-audit.json` y se convierte en una puerta obligatoria del despliegue público. Pruebas adversariales en `scripts/test_audit_frozen_2027.py` rechazan cambios en probabilidades, huellas, manifiesto o información posterior al corte de 2025. El conjunto de predicciones emitidas sigue siendo idéntico al registrado antes de 2027.

## GEO-2027 · Primera cohorte prospectiva pública emitida

Se ha añadido un protocolo científico para elaborar **antes de 2027** una primera cohorte prospectiva de **196 países**, prediciendo si en 2027 se registrarán **25 o más muertes anuales por violencia organizada de base estatal** en el campo `sb_total_deaths_best` del UCDP OrganizedViolenceCY. **No equivale a UCDP Onset `onset2`** ni a violencia gubernamental contra civiles: es una nueva pregunta científica y un horizonte fijo de dos años desde 2025.

Fuente de entrada: UCDP OrganizedViolenceCY 26.1, con datos hasta 2025 y SHA-256 publicado. Se congela una estimación Markov a dos pasos por país regularizada (prior 20), la tasa global de los últimos cinco años como referencia principal, el comparador Markov global, Brier como pérdida primaria y un criterio de resolución futura que impide convertir países ausentes en negativos.

**Estado actual:** primera cohorte de 196 probabilidades **emitida públicamente el 10 de noviembre de 2026 a las 17:23:12 UTC**, antes de comenzar 2027. La metodología estaba congelada en `main` desde las 17:20:43 UTC. La primera publicación íntegra corresponde al commit institucional `3bb3561c8d6182c30624591276c705fb76ce99dc`. SHA-256 inmutable del fichero `data/forecast-2027-ucdp261.json`: `5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5`. El commit `8b924e0b0c7a07e27977160c9658cfed77940aff` (17:32:54 UTC) preserva por primera vez el fichero **byte a byte idéntico** al producido por el generador, incluido el salto de línea final; el commit anterior `3bb3561c` ya publicaba las 196 probabilidades, pero sin ese terminador de archivo. Ambas publicaciones preceden a 2027. El manifiesto `data/forecast-2027-manifest.json` registra origen, estatus y corte. **No hay resultados oficiales observados de 2027, calibración demostrada ni evaluación prospectiva completada.** El commit de GitHub es un compromiso público verificable por hashes, pero **no** un sello de tiempo criptográfico de autoridad independiente.

Protocolo completo: `docs/forecast-2027-protocol.md`. Código y pruebas: `scripts/forecast_2027_statebased.py` y `scripts/test_forecast_2027_statebased.py`.

### Preparación de evaluación futura de GEO-2027

`scripts/evaluate_2027_official.py` proporciona un evaluador **offline, sin acceso a nuevos datos hasta su aportación explícita**. Exige los bytes íntegros y SHA-256 de la cohorte original, manifiesto de emisión, un ZIP oficial nuevo con etiquetas de 2027, URL y SHA-256 proporcionados para esa edición y una fecha de publicación posterior al cierre de 2027. Rechaza duplicados país-año, esquemas incompatibles y fuentes sin observaciones de 2027. No trata países ausentes como 0, reporta denominadores y bloquea puntuaciones si se resuelve menos del **95 %** de los 196 países.

Cuando exista una fuente futura, calculará Brier, log-loss, comparación contra ambas referencias congeladas y bootstrap de 2.000 repeticiones, sin entrenar de nuevo ni modificar probabilidades. El resultado queda etiquetado **SELF_REPORTED_OFFICIAL_SOURCE_NEEDS_FIRST_RELEASE_ATTESTATION** hasta comprobar externamente la fecha y el carácter de *primera edición* oficial. Este software **no implica que hayan aparecido resultados de 2027**: los ejemplos en `scripts/test_evaluate_2027_official.py` son sintéticos.

## Navegación

| Grupo | Vistas | Función pública |
| --- | --- | --- |
| Inicio | Resumen | Estado, líneas científicas y siguientes pasos |
| Predicciones | Explorador; Riesgos 2027 | Árbol sintético, supuestos y protocolo de emisión |
| Investigación | Mapa; Líneas y fuentes; Evidencia; Registro; Hitos | Estudios de demostración, Brier score, baselines y trazabilidad |
| Crear | Catálogo recuperado; Nuevas ideas; Estudio audiovisual | Cartera histórica institucional depurada (9 proyectos, 14 relaciones), borradores locales y guion de texto |

**Investigación institucional:** siete líneas de preguntas científicas con fuentes primarias, comparadores y condiciones pendientes. El CSV local permite comprobar fórmulas y un orden temporal declarado; la fecha real de publicación no se certifica y todavía no existe evidencia de utilidad predictiva prospectiva validada.

**Catálogo de ideas recuperado:** proviene del archivo histórico aportado al proceso de migración. Se publican nueve proyectos (cuatro vertientes V1–V4, tres aplicaciones y dos fichas de estructura), ocho fichas documentadas y catorce relaciones. La publicación usa una **proyección de campos permitidos**: elimina rutas, enlaces a PR antiguos, identificadores personales y referencias de implementación heredadas. Sus estados y fechas son históricos, no acreditan ejecución actual, nuevos experimentos ni pronósticos.

**Límites de esta versión:** no contiene los históricos reales, catálogos de países, predicciones de cohortes, modelos calibrados con observaciones oficiales ni los componentes de generación audiovisual. Tampoco permite escritura en un backend: las ideas se generan en memoria y pueden exportarse localmente. Ninguna cifra sintética es una previsión real.

## Cuaderno de investigación desde la web

La nueva ruta pública `/trabajo.html` ofrece una **herramienta local de investigación**, separada del conjunto sintético de divulgación. Permite importar archivos JSON privados elegidos por el usuario y verificar sus hashes SHA-256 en memoria, crear hipótesis no emitidas y exportar un cuaderno JSON. La política CSP bloquea las conexiones de red en esa ruta; el cuaderno **no lee Google Drive, no emite predicciones, no hace sellados RFC3161 y no es la custodia institucional canónica**. Para preservar una nueva actividad debe exportarse y admitirse explícitamente en el archivo institucional privado. No se almacena contenido privado en GitHub Pages ni en el repositorio.

### Comparación histórica por país

En el cuaderno `/trabajo.html` se puede importar un archivo JSON local que contenga los catálogos originales retrospectivos 2016 (195 países) y/o 2020 (196 países), ya sea en `futuresCatalogs` o dentro de las notas experimentales del archivo canónico de once tablas. Un validador rechaza catálogos parciales, variantes con metadatos inconsistentes y cualquier intento de tratarlos como emisiones prospectivas.

El panel **Árbol predictivo · comparación entre países** superpone de uno a seis países con colores, trazos y leyendas diferentes, compara las probabilidades anuales para el fenómeno seleccionado y permite inspeccionar sus cuatro estados `00/01/10/11`. El modelo por defecto utiliza conteos específicos de cada país con regularización global (`country_shrinkage`); otros modelos pueden coincidir exactamente para países con igual estado de origen y eso se representa sin alterar los resultados. Los gráficos se calculan únicamente en memoria desde los archivos que aporta el usuario; no se suben países, trayectorias ni probabilidades privadas a GitHub Pages o Drive. Son resultados **retrospectivos sobre una edición revisada**, no emisiones acreditadas ni evidencia de habilidad prospectiva.

## Árbol de países sin importaciones manuales

La vista **Predicciones → Explorador** utiliza desplegables de **Sociedad, Pregunta, Origen, Modelo y Año**. Obtiene automáticamente un fichero estático de distribución pública, generado en CI desde el **CSV oficial UCDP OrganizedViolenceCY 26.1** (CC BY 4.0, 7.132 filas), con la edición y la suma SHA-256 documentadas. El script `scripts/build_official_countries.py` computa por separado los conteos de transición a partir de los países presentes en cada fecha de corte (2014 y 2018): no carga expedientes del laboratorio privado, no usa resultados después del corte para ajustar parámetros, y no traslada identificadores ni textos de archivos personales. El resultado reproducible está disponible como `/data/countries-ucdp261.json` solo en GitHub Pages, nunca en el historial fuente.

**Distinción científica fundamental:** estos árboles son **reconstrucciones retrospectivas con la edición UCDP 26.1, publicada en 2026**, no predicciones prospectivas emitidas en 2016/2020 ni una copia certificada de los catálogos históricos privados. Para comparar cifras exactas del registro sellado original hay que seguir utilizando la custodia privada institucional.

## Inspección de ediciones históricas UCDP (10-11-2026)

La fuente oficial publica un índice de ediciones históricas del conjunto **Intrastate Country Level Onset**. La utilidad `scripts/inspect_ucdp_archives.py` inspecciona dicho índice, lista las rutas efectivamente enlazadas y valida las ediciones 23.1 y 25.1 frente a sus hashes SHA-256 registrados. Produce solo estadísticas de metadatos (esquema, cobertura temporal, recuentos y hash), sin datos personales ni historiales por país. La inspección se ejecuta en un job independiente de PR y **no** forma parte de GitHub Pages.

**Restricción de inferencia**: la existencia actual de un archivo de edición antigua no prueba cuándo exactamente fue publicado ni si una versión 22.1 estaba disponible antes de 2023. Sin prueba de disponibilidad previa, un estudio a posteriori sigue siendo una comparación *cross-release* retrospectiva. No se certifica emisión prospectiva.

**Hallazgo reproducido en GitHub Actions 10-11-2026, ejecución 42848508792**: los CSV oficiales UCDP Onset 23.1 (12.161 país-año, hasta 2022) y 25.1 (12.553, hasta 2024) coinciden con las huellas SHA-256 institucionales. Comparando únicamente los 12.161 país-año hasta 2022, `onset2` cambia en **2 casos** (2018, 0→1; 2021, 1→0). No cambian la cobertura de países-año en el periodo común ni los **242** positivos agregados, aunque sí la identidad temporal de dos etiquetas. 1946–1989: 0 cambios; 1990–2009: 0; 2010–2020: 1; 2021–2022: 1.

El índice oficial incluye el CSV 24.1, pero su URL respondió **HTTP 404** en el job de investigación; la edición 22.1 no aparece enlazada. Este estado refleja únicamente esa comprobación puntual y puede cambiar si UCDP repara el archivo. Por ello **aún no es posible certificar una evaluación multianual point-in-time** usando la cadena de fuentes Onset prevista. El resultado de revisiones se publica en la sección *Investigación → Evidencia*, separado de las pruebas sintéticas y de la validación de capacidad predictiva.


## Q-GEO-01 · Auditoría de unidades y tasas recientes (10-11-2026)

**Revisión del estudio mixto de 715 países-año:** el archivo `onsets_computed.csv` enlazado como Onset 19.1 contiene 47 duplicados país-año, 13 discordantes. El conjunto posterior **Intrastate Country Level Onset** exige por diseño un único registro por país-año. Agregar las observaciones antiguas con OR no certifica equivalencia de las etiquetas ni de los países en riesgo. Por consiguiente, el resultado −8,94 % de aquel experimento permanece **solo como diagnóstico exploratorio de archivos heterogéneos** y no debe citarse como validación independiente comparable. Véase la documentación de UCDP sobre niveles *conflict* y *country* en `https://ucdp.uu.se/downloads/onset/ucdp-codebook-onset-221.pdf`.

Para evitar el cambio de unidad, `scripts/experiment_recency_onset.py` utiliza **únicamente las ediciones Intrastate Country Level 23.1 y 25.1**, comprobadas por SHA-256. La rejilla fija de candidatos, planteada **después** de mirar los primeros resultados, compara las tasas globales calculadas sobre 5, 10, 20 años e histórico completo; aplica también un modelo regularizado por país con prior 20 sobre cada una de esas tasas. Presenta los ocho modelos en su totalidad y **no selecciona** el mejor para alegar una prueba nueva.

| Muestra | N país-año | Inicios `onset2` | Precaución |
|---|---:|---:|---|
| Ventanas internas 2015–2022 | 1.568 | 22 | Edición 23.1 revisada, **no as-of** |
| Comparación externa 2024 | 196 | 1 | Edición 25.1 como etiquetas, **resultado ya visto** |

En el contraste externo de 2024, el Brier de la **frecuencia global 5 años** es **0,005142209**, ligeramente inferior al global histórico **0,005201040**. El Brier del **modelo por país con prior de 5 años** es **0,005285406**, peor que el global. En la muestra interna, el Brier agregado del global completo es **0,013845771**, frente a **0,013888438** del modelo por país completo. Con un solo inicio en 2024, seleccionar un vencedor entre ocho variantes equivaldría a *selection bias*. El log-loss puede ordenar los modelos de forma diferente y se muestra por separado.

**Pruebas y trazabilidad:** Actions `42859240878`, scripts `experiment_recency_onset.py` / `test_experiment_recency_onset.py`; la investigación pública expone agregados en `data/research.json`. El experimento retrospectivo no contiene emisiones; la nueva cohorte GEO-2027 es independiente, está emitida y tiene 0 resultados resueltos. No hay pruebas confirmatorias nuevas. Próximo paso científicamente defendible: emitir y sellar prospectivamente predicciones antes de un nuevo periodo objetivo y validarlas cuando se publiquen resultados.

## Q-GEO-01 · Contraste real entre ediciones 2017/2022 (10-11-2026)

La herramienta institucional `scripts/run_legacy_vintage_holdout.py` calcula, sin descargar ni publicar datos del repositorio personal, un experimento **ex post** con tres CSV históricos oficiales UCDP verificados por SHA-256. Ajusta tasas globales y por país (regularización 20) desde 2000 hasta el último año **realmente contenido** en cada archivo, sin utilizar las etiquetas del año objetivo durante el entrenamiento. Compara 2020–2022 (archivo enlazado bajo Onset 19.1 → resultados de 23.1) y 2024 (23.1 → 25.1).

| Año | Países-año | Inicios `onset2` |
|---|---:|---:|
| 2020 | 173 | 2 |
| 2021 | 173 | 1 |
| 2022 | 173 | 3 |
| 2024 | 196 | 1 |
| **Total** | **715** | **7** |

**Resultado descriptivo NO HOMOGÉNEO**: los ficheros pueden utilizar unidades de observación distintas. Sus resultados no constituyen una prueba válida de capacidad prospectiva comparable. Brier del modelo por país **0,011100848419**, baseline de frecuencia global **0,010190138316**, referencia trivial siempre cero **0,009790209790**; Brier Skill frente a global **−8,94 %**. Log-loss del modelo **0,067702071233**, global **0,064953305637**. El intervalo exploratorio mediante 2.000 bootstrap por país para Brier país menos global fue **[+0,000199329, +0,001657918]**. Esto no permite afirmar superioridad y no constituye validación confirmatoria.

**Limitaciones materiales que no deben ocultarse:** el CSV que UCDP enlaza bajo 19.1 termina realmente en **2017**, aunque su codebook se refiere a 2018. Contiene **47 claves país-año duplicadas**, 13 con `onset2` contradictorio. Se aplicó una transformación OR («al menos un inicio») y, como sensibilidad exploratoria post hoc, se excluyeron todas las claves duplicadas: 516 observaciones, Brier Skill **−7,43 %**. La limpieza modifica la población al perder un país de referencia; no se presenta como prueba confirmatoria. No hay certificación criptográfica de las fechas de publicación originales, ni se garantiza paridad completa de las definiciones entre ediciones, ni se emitieron pronósticos en los años objetivo.

Experimento reproducible: ejecución de Actions `42856960583`, pruebas `scripts/test_run_legacy_vintage_holdout.py` y estudio agregado `data/research.json` (`external_vintage_holdout`). La web solo publica métricas agregadas, fuentes y advertencias. **Pronósticos prospectivos verificados: 0**.

## Evaluación temporal Q-GEO-01 (experimental)

`src/temporal-validation.mjs` implementa un evaluador **offline** de país-año mediante rolling-origin, con ventana de test predefinida, embargo de etiquetas, disponibilidad declarada de fuentes y estado previo, comparadores global y condicional, regularización jerárquica por país, métricas Brier/log-loss, calibración descriptiva y alertas con cupo fijo. Sus pruebas adversariales están en `tests/temporal-validation.test.mjs`.

**Este evaluador local no ha emitido predicciones verificadas**: sus pruebas de unidad siguen empleando ejemplos sintéticos; el contraste retrospectivo real entre ediciones se ejecuta mediante el script institucional independiente documentado en el apartado anterior. Las fechas y hashes de entrada no se autentican automáticamente: el resultado permanece etiquetado `RETROSPECTIVE_ROLLING_ORIGIN_ASOF_SELF_REPORTED`. No se publica el código del evaluador en Pages ni se mezclan archivos personales. El contraste real entre UCDP 23.1/25.1 de 2024 continúa siendo no concluyente: Brier peor y log-loss mejor que el baseline, con un solo evento.

## Ejecución

Sitio HTML/CSS/JS sin framework ni dependencias externas. Para previsualizarlo, servir la carpeta mediante un servidor estático (por ejemplo, `python3 -m http.server 8000`) y abrir la raíz del servidor. No abrir `index.html` directamente mediante `file://`, porque la carga del JSON usa `fetch`.

```bash
node --test tests/*.test.mjs
python3 scripts/audit_public.py
```

GitHub Actions ejecuta las pruebas, comprueba los autores, audita el árbol público y publica exclusivamente `index.html`, `styles.css`, `logo.svg`, `favicon.svg`, `src/site.mjs`, `src/metrics.mjs` y `data/demo.json`, así como `src/research.mjs` y `data/research.json`, además de `src/project-catalog.mjs`, `src/project-portfolio.mjs` y `data/projects.json` depurado. El paquete público incluye ahora además el manifiesto y las 196 probabilidades GEO-2027, con verificación de SHA-256. Ningún README, workflow, archivo de desarrollo o configuración de repositorio forma parte del paquete desplegado.

## Requisitos para datos reales

Toda observación requiere licencia de redistribución, fuente primaria, fecha de publicación, edición temporal recuperable y protocolo de evaluación. Los pronósticos necesitan fecha de emisión verificable anterior al desenlace y comparación con un baseline. Las evaluaciones retrospectivas no se presentarán como pruebas prospectivas.

El sitio es una demostración pública autocontenida: no incorpora credenciales, endpoints de acceso privado ni datasets experimentales. Se auditan sus activos y dependencias antes de cada publicación.

© IDEA LAB. Derechos reservados salvo indicación expresa.
