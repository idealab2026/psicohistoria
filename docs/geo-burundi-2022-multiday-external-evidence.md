# Burundi 2022: auditoría exploratoria de un acontecimiento de tres días

**Experimento secundario fechado 19/11/2026.** Este análisis NO corrige ni reinterpreta como 3/3 o como nuevo denominador la auditoría **primaria** publicada en PR #130. El episodio UCDP GED 25.1 n.º **442626**, en **Burundi (GWNO 516)**, fue excluido legítimamente de aquella auditoría por no tener fecha única: los eventos con intervalo se analizarían únicamente mediante un segundo protocolo.

## Objeto, evidencia y distinción de fuentes

| Propiedad | Evidencia de origen | Fiabilidad / interpretación |
|---|---|---|
| Evento GED | UCDP GED25.1, ID 442626 | Un registro estatal (tipo 1) |
| País-año | Burundi, 2022 | Mismo GWNO que el modelo country-year |
| Inicio y final | 19–21 junio 2022 inclusive | Intervalo, NO una fecha puntual |
| Fallecidos `best` | 10 | Estimación editorial, no identificación forense |
| Localización GED | lat −2,708333, lon 29,243056 | Geopunto GED; precisión sujeta a codificación |
| Antigua → nueva CY | 0 → 10 (UCDP23.1→24.1) | Misma institución; no independencia |

### Documentación encontrada

**[SOS Médias Burundi, 21 de junio de 2022](https://www.sosmediasburundi.org/2022/06/21/cibitoke-une-dizaine-de-morts-et-plusieurs-blesses-decouverts-a-la-kibira/).** Reportaje contemporáneo de David Irakoze, en el que fuentes militares y locales refieren enfrentamientos durante tres días en Kibira/Mabayi (Cibitoke), con **diez muertos y ocho heridos** en el bando rebelde. Algunas declaraciones atribuyen las muertes a fuerzas militares ruandesas o identifican a los fallecidos con FLN, pero **son atribuciones de fuentes**, no una identificación indiscutida de autores/víctimas.

**[International Crisis Group, CrisisWatch: junio de 2022](https://crisisgroup-staging-3.sbx.so/crisiswatch/july-alerts-and-june-trends-2022).** Resumen retrospectivo publicado después de junio, que consigna combates **19–21 de junio**, Mabayi/Cibitoke y el mismo balance de **diez muertos y ocho heridos**. Es una **fuente institucional secundaria**, posiblemente basada en el mismo periodismo de SOS Médias Burundi: **dos instituciones citando diez víctimas no implican dos testigos independientes**.

Se preservan las URLs, las fechas, los autores cuando constan y las cautelas en el informe. Son documentos públicos; no se copian artículos íntegros ni se asigna el número de víctimas a GDELT.

## Método fijo de la ampliación exploratoria

Se comprueba SHA-256 del ZIP original GED25.1 (de la PR #130) y se reextrae el único evento 442626, exigiendo exactamente tipo 1, best 10, GWNO 516, inicio 2022-06-19, fin 2022-06-21 y coordenadas preestablecidas.

Se descargan cuatro archivos originales `YYYYMMDD.export.CSV.zip` de **GDELT 1.0**: los días 19, 20, 21 y 22 de junio de 2022. El 22 se considera estrictamente **día adicional de incorporación/publicación**, nunca una cuarta fecha de enfrentamientos. Se distinguen `SQLDATE` (fecha inferida del acontecimiento), la fecha del archivo diario y `DATEADDED` de GDELT.

Los filtros de la auditoría son: `ActionGeo_CountryCode=BY` (Burundi; FIPS, no código de actores CAMEO), `EventRootCode∈{18,19,20}` (acción violenta codificada) y `SQLDATE` dentro de 19–21. Se muestran también por separado registros con `SQLDATE=22`, no contados como coincidencia estricta. Las distancias al geopunto GED se evalúan en **25, 100 y 250 km** y se discriminan los tipos de geocodificación GDELT, separando coordenadas aproximadas de centroides nacionales (`ActionGeo_Type=1`). Las filas se deduplican por `GLOBALEVENTID`, los dominios de noticias solo se usan como pistas para verificación manual, no como testigos independientes. Los cuatro ZIP quedan verificados por SHA-256 en cada reproducción.

**Interpretación:** una fila GDELT geográfica en fecha y radio es una posible huella informativa, no prueba de identidad del episodio ni de muertos. Un resultado sin coincidencias tampoco descarta los enfrentamientos. No se confunden **10 víctimas UCDP**, **10 noticias** y **10 eventos GDELT**. La concordancia de fuentes puede deberse al mismo testimonio primario, incluida una eventual dependencia entre GDELT y SOS.

## Criterio de éxito y límites

El estudio puede cuantificar cuántas noticias violentas codificadas se sitúan temporal y espacialmente cerca del GED, ofrecer fuentes candidatas para auditoría humana y asegurar que no se incorpora el evento multi-día al denominador principal. **No puede convertir el riesgo H2 emitido en "acertado" ni recalibrar el modelo con un caso elegido después de detectar la revisión.**

La tabla de resultados y las huellas SHA se añadirán después del primer replay de CI, en `data/geo-burundi-2022-multiday-independent-event-evidence.json`.

Fuentes técnicas: [UCDP historical releases](https://ucdp.uu.se/downloads/olddw.html) y [GDELT events 1.0](https://gdeltproject.org/data.html).

## Resultado publicado de la auditoría exploratoria

Los cuatro archivos diarios originales GDELT han sido descargados y fijados con SHA-256, junto con el evento 442626 de UCDP GED25.1. La reproducción estricta recupera las fechas 19–21 de junio de 2022, la clasificación **state-based (tipo 1)**, **10 fallecidos estimados** y las coordenadas originales **−2,708333, 29,243056**.

| Archivo diario GDELT | Registros globales | Acciones violentas codificadas con ActionGeo BY | Acciones violentas BY con SQLDATE del 19 al 22 de junio |
|---|---:|---:|---:|
| 19/06/2022 | 60.343 | 0 | 0 |
| 20/06/2022 | 98.444 | 1 | 0 |
| 21/06/2022 | 111.155 | 1 | 1 |
| 22/06/2022 | 122.325 | 0 | 0 |

El único registro con fecha inferida dentro de **19–21 junio**, GDELT `1050430960`, tiene CAMEO raíz **19** y procede de una URL cuyo dominio es `crisis24.garda.com`. Sin embargo, GDELT lo sitúa en el **centroide nacional de Burundi** (`ActionGeo_Type=1`), a **121,707 km** del punto GED. Esta coordenada es aproximada por definición: **no es una ubicación independiente del combate**.

| Criterio de evidencia GDELT | Registros encontrados |
|---|---:|
| Acciones violentas, país Burundi, SQLDATE 19–21/06 | 1 |
| De ellas a ≤250 km del punto GED | 1, pero centroide nacional |
| De ellas a ≤100 km del punto GED | **0** |
| De ellas a ≤25 km del punto GED | **0** |
| De ellas con geocodificación de ciudad, a ≤100 km | **0** |
| Casos con fecha inferida del día 22, contabilizados solo como lag | 0 |

**Resultado negativo del contraste automatizado geográfico.** Los archivos consultados no aportan una huella local suficiente para identificar el episodio de Mabayi. La única fila GDELT no debe contarse como corroboración geográfica a pesar de tener país, fecha y código de violencia compatibles.

**Resultado positivo del rastreo documental:** [SOS Médias Burundi (21/06/2022)](https://www.sosmediasburundi.org/2022/06/21/cibitoke-une-dizaine-de-morts-et-plusieurs-blesses-decouverts-a-la-kibira/) describió diez muertos y ocho heridos en los enfrentamientos de Kibira/Mabayi; [CrisisWatch de International Crisis Group](https://crisisgroup-staging-3.sbx.so/crisiswatch/july-alerts-and-june-trends-2022) consignó el mismo episodio y cifras en un resumen secundario. Se mantiene la **posible dependencia de las fuentes originales**; no se presenta como corroboración forense duplicada ni se infiere identidad exacta de los combatientes.

La revisión UCDP 23.1→24.1 del país-año Burundi 2022, **0→10**, es documentalmente rastreable a un acontecimiento compatible, sin establecer que cada uno de los diez fallecidos haya sido comprobado mediante testigos o expedientes independientes. El reporte anterior de la PR #130 sigue inalterado y con sus dos eventos puntuales elegibles.

**Resultado reproducible:** [JSON con metadatos GED, cuatro archivos GDELT y fuentes](../data/geo-burundi-2022-multiday-independent-event-evidence.json) · [código verificable](../scripts/audit_geo_burundi_2022_multiday_event_evidence.py) · [pruebas automáticas](../scripts/test_audit_geo_burundi_2022_multiday_event_evidence.py).

### Decisión científica

Para seguir avanzando hacia una validación genuinamente independiente, el próximo objetivo es localizar noticias con **autor o institución distintos y fuentes primarias comprobables** que describan el episodio del 19 al 21 de junio, y confirmar que no reproducen todas la crónica del mismo medio. Alternativamente, comparar un registro de eventos de una institución externa con protocolo de identidad de episodio, temporalidad y deduplicación. **No se recalibra GEO2027 ni se actualizan sus probabilidades por esta evidencia retrospectiva.**
