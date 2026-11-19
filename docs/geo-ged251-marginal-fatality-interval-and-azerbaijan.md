# PSICOHISTORIA · Intervalos de fallecidos GED25.1 y revisión de Azerbaiyán 2021

**Diseño cerrado el 19/11/2026 antes de examinar los límites low/high de los 118 eventos.** Se continúa desde la [PR #142](geo-ged251-togo2022-pivotal-source-genealogy.md), que identificó una sensibilidad matemática importante en Togo 2022: al reemplazar best=23 por low=8 en una única fila, el total del país pasaría de 34 a 19.

## Pregunta

¿En cuántos de los **14 países-año previamente seleccionados** con best estatal entre 15 y 35 fallecidos puede cambiar la clasificación binaria `≥25` cuando se consideran **las propias estimaciones low, best y high de UCDP GED25.1**? ¿Cuántos dependen exclusivamente de una fila de estimación incierta? Esta pregunta distingue **incertidumbre de medición publicada por la fuente** de errores reales de codificación o duplicación documental.

### Selección fijada, sin dependencia de low/high

- Población: **los mismos 14 GWNO-año de 2021 y 2022**, exactamente **118 filas de violencia tipo 1**, de la banda best `15..35` preregistrada en la [PR #137](geo-ged251-near25-countryyear-census.md) y verificada después en la [PR #141](geo-ged251-near25-source-publication-lag-census.md).
- ZIP oficial UCDP GED25.1, SHA-256 `e256f1fb20a579d8b2f910e5bae212f486d3002adaa2e4359ace740c737da05d`. Reproducir los **IDs originales** de cada país-año y el total best antes de calcular intervalos.
- Para cada país-año, sumar `low`, `best`, `high` de todas las filas de violencia estatal tipo 1, **incluidas las de best=0, las no geocodificables y las que no tienen fecha de publicación**. Exigir `low <= best <= high` individualmente.
- Clasificación: *negativo bajo las tres estimaciones* (`high <25`), *positivo bajo las tres* (`low >=25`) e *indeterminado entre límites* (`low <25<=high`). Se registran por separado desacuerdos best-vs-low y best-vs-high.
- Control adicional: variar el `best` de **una fila cada vez** a su `low` o `high`, dejando en best las demás, y contar país-años en que ese reemplazo hipotético mueve la etiqueta. **No seleccionar los países tras ver estos resultados.**
- No cuantificar errores globales de UCDP ni precisión de GEO a partir de la cohorte condicional a best. **La suma de intervalos de fuentes no es un intervalo probabilístico conjunto**. Es una envolvente aritmética de escenarios extremos que pueden estar correlacionados, resultar incompatibles documentalmente o no reflejar incertidumbre real conjunta.

### Control de fecha previamente identificado: Azerbaiyán

GED **427299**, GWNO **373**, evento estatal con best=1 de fecha exacta **17/06/2021** y **una cita bibliográfica fechada el 06/06/2021**. Se fija como control adicional antes de consultar el título y la procedencia del documento original: obtener de GED25.1 el titular, emisor, fecha, actores, lugar, díada y desglose low/best/high, conservando una huella SHA-256 bibliográfica. **No decidir que la fecha del hecho es falsa** por una publicación anterior sin comprobar si esa noticia trata de un episodio distinto o de contexto previo.

El año Azerbaiyán 2021 consta con best=30 en la cohorte anterior; eliminar hipotéticamente el registro de una muerte no cruza 25, por lo que la prioridad de este caso es documental, **no** de estabilidad individual de etiqueta.

## Enmienda de protocolo tras la primera ejecución (documentada en Git)

**La preregistración inicial contenía un supuesto metodológico incorrecto:** que cada fila GED respetaría siempre `low ≤ best ≤ high`. La primera ejecución sobre el archivo oficial no superó ese control. La consulta del [codebook oficial UCDP GED25.1, §5.5, página 23](https://ucdp.uu.se/downloads/replication_data/2025_ucdp-ged-251.pdf) reveló que las filas `event_clarity=2` pueden contener un `high` inferior a `best` o `low`, porque la estimación agregada se corrige al identificar episodios claros que ya se contabilizan por separado.

No se debe transformar ese comportamiento oficialmente documentado en un «error» de UCDP ni excluir las filas. **La enmienda conserva el universo congelado de 14 países-año y 118 IDs, pero modifica la fórmula**, antes de calcular nuevos resultados:

1. Reproducir por separado las sumas **literales** de `low`, `best` y `high` de las filas oficiales, sin reordenarlas ni llamar «intervalo ordenado» a las tres.
2. Calcular una **envolvente aritmética descriptiva** sumando el mínimo y el máximo de las tres estimaciones de **cada fila**. Esta envolvente contiene necesariamente best incluso en eventos agregados no monótonos, pero **no es un intervalo estadístico de confianza ni asegura consistencia conjunta**.
3. Publicar cuántos eventos presentan orden no monótono, su `event_clarity`, los valores originales y en qué país-año ocurren; comparar también cada escenario literal `low` y `high` con la etiqueta basada en `best`.
4. Mantener el test de entradas ordenadas para la función de clasificación sobre **mínimo/best/máximo normalizados**, no como requisito indebidamente impuesto a las filas originales.

**Control de transparencia:** el fallo inicial, esta corrección y la reproducción posterior quedan visibles en el historial de commits y CI de la PR. No se modifican los datos oficiales para forzarlos a superar un test artificial.

## Límites y reproducibilidad

El informe estructurado se congelará en [JSON](../data/geo-ged251-marginal-low-best-high-2021-22.json) tras la primera ejecución SHA-verificada, y CI comprobará luego coincidencia exacta.

- `python3 -B -m unittest discover -s scripts -p 'test_audit_geo_ged251_marginal_fatality_interval.py' -v`
- `python3 -B scripts/audit_geo_ged251_marginal_fatality_interval.py --check-report`
- `python3 -B scripts/audit_public.py`

**Regla de interpretación:** los límites low/high provienen de una edición **retrospectiva de 2025**, por tanto no son datos as-of históricos para entrenar predicciones retrospectivas sin corte de fuente. No se cambia ningún registro histórico ni las probabilidades prospectivas GEO2027/GEO2028. No se afirma una mejora de Brier ni una habilidad predictiva nueva.

## Resultados SHA-verificados · Censo completo de 14 países-año

El archivo oficial GED25.1 volvió a reproducir los **118 IDs históricos y los 14 totales anuales best** sin ningún cambio en la cohorte previamente fijada. La envolvente aritmética normalizada da **4 país-años siempre positivos, 5 siempre negativos y 5 con umbral atravesado**. La clasificación se refiere únicamente a las alternativas numéricas codificadas en GED25.1, nunca a probabilidades sobre la verdad histórica.

| País-año | Suma low literal | Suma best | Suma high literal | Envolvente mín.–máx. por evento | Clasificación aritmética |
|---|---:|---:|---:|---:|---|
| Perú 2021 | 20 | 20 | 20 | 20–20 | Negativo |
| Azerbaiyán 2021 | 30 | 30 | 33 | **29–34** | Positivo |
| Benín 2022 | 30 | 30 | 33 | 30–33 | Positivo |
| **Togo 2022** | **19** | **34** | **59** | **19–59** | **Sensible** |
| Uganda 2021 | 22 | 22 | 22 | 22–22 | Negativo |
| Uganda 2022 | 25 | 25 | 28 | 25–28 | Positivo |
| **Burundi 2021** | **24** | **24** | **27** | **24–27** | **Sensible** |
| **Angola 2022** | **1** | **20** | **114** | **1–133** | **Sensible** |
| Argelia 2021 | 18 | 18 | 18 | 18–18 | Negativo |
| Túnez 2021 | 18 | 18 | 19 | 18–19 | Negativo |
| Sudán 2021 | 31 | 31 | 72 | 31–72 | Positivo |
| **Sudán del Sur 2022** | **23** | **23** | **30** | **23–30** | **Sensible** |
| Tayikistán 2021 | 16 | 16 | 16 | 16–16 | Negativo |
| **Tailandia 2022** | **23** | **29** | **29** | **23–29** | **Sensible** |

Las **sumas literales de high** en Angola y Azerbaiyán pueden ser inferiores a la envolvente máxima porque UCDP incluye dos filas con orden no monótono. Solo la envolvente min/max por evento se garantiza que contenga best. En Angola, best=20 y high literal=114, pero la envolvente da máximo 133.

**Desacuerdos respecto a best:** si todas las filas se sustituyen por sus valores `low`, cambian **2** país-años (Togo y Tailandia); si se sustituyen por `high`, cambian **3** (Burundi, Angola y Sudán del Sur). Cambiar solamente **una fila a la vez** es suficiente para cruzar la etiqueta en **un** país-año al elegir low (Togo) y **tres** al elegir high (Burundi, Angola y Sudán del Sur). En Tailandia se necesitan cambios de varias filas a low: no existe una única sustitución low de una fila que cambie por sí sola el estado anual.

### Dos filas GED con orden no monótono

| GED ID | País-año | Claridad | Low | Best | High | Interpretación |
|---|---|---:|---:|---:|---:|---|
| **464758** | Angola 2022 | **2** | 0 | 19 | 0 | La excepción del §5.5 de UCDP admite que el máximo bruto de un evento agregado resulte menor que best al eliminar subeventos identificados aparte |
| **423850** | Azerbaiyán 2021 | **1** | 7 | 7 | 6 | **No encaja directamente** en la justificación de claridad=2 del manual; requiere investigación específica, pero no implica por sí solo un error confirmado |

La excepción de claridad=2 está documentada literalmente en el [codebook oficial GED 25.1, página 23, §5.5](https://ucdp.uu.se/downloads/replication_data/2025_ucdp-ged-251.pdf). No se impuso artificialmente la ordenación sobre las fuentes; las filas permanecen intactas y se conserva el identificador para revisión posterior.

**Consideración sobre Uganda:** la envolvente 25–28 es estable sobre los números codificados, **pero esa estabilidad no resuelve la elegibilidad de sus dos muertes policiales de junio**. No equiparar robustez de estimación numérica condicionada a inclusión de la fila con robustez a errores de clasificación del tipo de violencia.

## Azerbaiyán 2021: publicación anterior al suceso y posible fecha de descubrimiento

El registro oficial **GED 427299** está codificado como fallecimiento civil de tipo 1 en la díada **Gobierno de Azerbaiyán – República de Artsaj** (GWNO 373), lugar **Agdam rayon**, precisión geográfica **4** y fecha temporal exacta **17/06/2021** (`date_prec=1`), con low=best=high=1. Solo contiene una referencia bibliográfica: **Fiscalía General de Azerbaiyán, 06/06/2021**, con titular sobre una investigación de la muerte de un civil por mina. **No se ha localizado un documento íntegro de Fiscalía del día 6 que identifique a la misma persona.**

Dos noticias publicadas el **17/06/2021** ofrecen información más detallada sobre un único fallecimiento de un civil por mina en Agdam:

- [APA, 17/06/2021](https://apa.az/en/xeber/accidents-incidents-news/43-year-old-man-missing-in-aghdam-found-out-to-be-killed-in-mine-explosion-351875): reporta que se encontró muerto a un hombre desaparecido hacía más de diez días, por explosión de una mina cerca de Seyidli, Agdam.
- [Report.az, 17/06/2021](https://report.az/en/karabakh/body-of-landmine-victim-in-aghdam-handed-over-to-his-family): atribuye a las autoridades locales que había desaparecido **el 7 de junio**, se encontró su cadáver **el 16** y se entregó a su familia el **17**.

Ambos medios se apoyan en **fuentes de las fuerzas de seguridad de Azerbaiyán**; no constituyen testimonios periciales independientes de la hora del fallecimiento. Las publicaciones presentan **un fallecimiento que precede al 17 de junio** y un día de descubrimiento público distinto del día de la muerte, **pero aún no está demostrado** que sus noticias describan exactamente el mismo evento al que UCDP vinculó la referencia del **6 de junio**. De confirmarse identidad, `date_prec=1` fijado en el 17 necesitaría revisión porque el fallecido llevaba desaparecido desde días antes.

**Cuestión adicional:** las minas que permanecen tras una guerra pueden matar civiles después del cese del combate. Es necesario determinar si esta muerte cumple la definición concreta de **violencia estatal vinculada a enfrentamiento armado organizado**, no asumir que toda mina dentro de un territorio en disputa entra automáticamente en el modelo. Los documentos consultados no prueban independientemente quién colocó la mina ni cuándo.

**Estado:** referencia bibliográfica y exactitud de la fecha GED **indeterminadas**; posible fecha de comunicación o hallazgo confundida con fecha de muerte, **no corregida**. La reducción hipotética de una muerte en Azerbaiyán (best=30→29) **no cambia la etiqueta**. Esta discrepancia es valiosa para calidad de datos, pero menos prioritaria para el target binario que Togo, Angola o Sudán del Sur.

La anotación pública verificable está en [JSON de revisión documental de Azerbaiyán](../data/geo-ged251-azerbaijan-2021-external-date-review.json). Ninguna referencia de prensa ha sido archivada con una huella SHA propia y ninguna víctima ha sido reconciliada mediante parte forense independiente.

### Implicación sobre el forecasting

De **14 país-años seleccionados por estar cerca de 25**, **5 son sensibles a escenarios low/high internos** y **9 no lo son** bajo los extremos aritméticos publicados. **No puede extrapolarse 5/14 a los 392 país-años ni a 196 países futuros**, pues existe selección condicionada al total best. Tampoco puede aplicarse la información de GED25.1, producida retrospectivamente, como predictor disponible en años anteriores.

Antes de dar por válida una etiqueta de entrenamiento debería adoptarse una evaluación de sensibilidad del scoring bajo definiciones de etiquetas alternativas, congeladas por cohorte y as-of, y un protocolo transparente de discrepancias no adjudicadas. **En este estudio no se recalcula el Brier ni se declara mejor habilidad predictiva.**
