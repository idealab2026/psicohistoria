# PSICOHISTORIA · Retraso de publicación frente a fecha del hecho (GED25.1)

**Protocolo registrado el 19/11/2026 antes de extraer los metadatos de fechas de publicación de la cohorte.** Continuación de la [PR #140](geo-ged251-uganda-december-2022-source-reconciliation.md), que identificó dos **posibles discrepancias día-del-hecho vs día codificado** en Uganda 2022.

## Concepto científico crucial

El manual oficial [UCDP GED Codebook 25.1](https://ucdp.uu.se/downloads/ged/ged251.pdf) define **source_date como fecha de publicación del material**, mientras **date_start/date_end** representan el intervalo de ocurrencia y **date_prec** su precisión. El valor de publicación **1753-01-01** es un código de *fecha faltante*, no una noticia del siglo XVIII. Esta investigación no confunde el desfase normal de una noticia publicada al día siguiente con un error de codificación.

Por ejemplo, publicar el 20 de diciembre una noticia sobre un hecho del 19 es perfectamente normal; publicar el 20 una noticia donde el texto declara expresamente que el hecho sucedió el 18 y que el registro GED lo fecha el 19 merece revisión documental. La primera observación no permite deducir la segunda.

## Universo fijado antes del cálculo

- Los **14 países-año, 2021–2022**, y su marco GEO2027 de 196 GWNO seleccionados previamente en la [banda 15–35 fallecidos](geo-ged251-near25-countryyear-census.md). **No** se seleccionan observaciones en función de sus fechas de noticias o de su probabilidad GEO.
- Todas las filas oficiales GED25.1 de violencia **tipo 1**, incluido best=0 y las no geocodificables. No se limita arbitrariamente a fechas exactas ni a eventos con más de cero muertes: los denominadores se reconstruyen con recuentos y sumas **best** fijados por la PR #137.
- Fuente: ZIP UCDP GED25.1 con SHA-256 **e256f1fb20a579d8b2f910e5bae212f486d3002adaa2e4359ace740c737da05d**. El programa revalida el repositorio y las emisiones originales de GEO2027, además de la genealogía previa de Burundi.
- Campos originales: GED_event_id, GWNO, año, best, date_start, date_end, date_prec y source_date. Cada evento puede citar varios materiales, por tanto **source_date contiene fechas separadas por punto y coma**; se obtienen fechas válidas, tokens no interpretables y valores faltantes sin imputar.
- **1753-01-01 se excluye** de los cálculos de retraso. Se conserva su frecuencia, al igual que los tokens no parseables y las filas sin fecha válida.
- Para cada evento se miden los días entre **primera publicación conocida** y **final del intervalo de hecho codificado**: publicación previa al inicio, publicación dentro del intervalo, +1 día, +2–7, +8–30, +31 o más, o sin datos.
- Se separan todos los eventos y el subgrupo con `date_prec=1` y ventana de exactamente un día. Para las **13 filas de eliminación individual teóricamente pivote** previamente identificadas se publican las mismas categorías, sin presuponer que haya error real.
- Dos casos de **Uganda diciembre 2022** (GED 460859 y 462156) tienen **fecha explícita del evento en fuentes contemporáneas** distinta en un día de la fecha exacta GED. Se incorporan como **controles previamente revisados**, no como resultado descubridor de una nueva búsqueda, y nunca se infieren a partir de `source_date`. Su revisión detallada está en la [PR #140](../data/geo-ged251-uganda-2022-december-public-source-review.json).
- Se declaran **cero errores de codificación validados** y **cero correcciones**. Todo alerta detectada es candidata a contrastar texto por texto, nunca identificación automática de un fallo.

## Interpretación y límites

Una referencia anterior al comienzo de un episodio puede ser una noticia contextual, un hecho de varios días o una equivocación de indexación. Un artículo publicado un año después puede ser una retrospectiva, no un desfase de registro. **Sin leer el contenido y establecer qué fecha concreta describe cada fuente no existe una medida de errores de codificación**. Este censo es condicional a 14 unidades próximas al umbral y nunca representa la prevalencia de errores del conjunto mundial.

**Salida programática:** [JSON del censo de publicaciones y controles históricos](../data/geo-ged251-marginal-source-publication-lags-2021-22.json).

Reproducir (cuando el JSON haya quedado congelado por commit):

- `python3 -B -m unittest discover -s scripts -p 'test_audit_geo_ged251_marginal_source_date_lags.py' -v`
- `python3 -B scripts/audit_geo_ged251_marginal_source_date_lags.py --check-report`
- `python3 -B scripts/audit_public.py`

La calidad de información bibliográfica se mide usando la edición *retrospectiva* GED25.1 (extracción en 2025). **No** debe incorporarse como feature del modelo predictivo as-of 2021/22 ni utilizarse para reclamar mejora de Brier GEO2027/GEO2028.

## Resultado oficial reproducido · 19/11/2026

El ZIP oficial GED25.1 con SHA-256 fijado se ha reproducido para **los 14 países-año marginales** (2021–2022) y **todas sus 118 filas de violencia tipo 1**, de las cuales **98** constan como fecha exacta (date_prec=1, un día). Se han reproducido exactamente los totales de fallecidos y las 13 filas matemáticamente decisivas previamente congeladas; **cero etiquetas modificadas**.

| Primera publicación conocida frente a fecha del hecho GED | Filas GED | Interpretación |
|---|---:|---|
| Antes del inicio del intervalo | **2** | **Candidatos de revisión bibliográfica**, nunca error probado |
| Dentro del intervalo | **63** | Normal para cobertura contemporánea |
| +1 día después del fin del intervalo | **26** | Retraso normal; no se recodifica |
| +2–7 días | **12** | Retraso moderado |
| +8–30 días | **10** | Prensa posterior o consolidación |
| +31 o más días | **4** | Posible fuente retrospectiva |
| Sin fecha de publicación válida | **1** | No imputar fecha |
| **Total** | **118** | Selección condicional 15–35 muertes |

No se encontraron fechas `1753-01-01` ni tokens no interpretables en estas filas, pero el parser **excluye explícitamente** ese marcador y registra su frecuencia; en una fila falta información utilizable de la fecha de fuente.

### Casos donde la publicación conocida precede al evento GED

| País y año | Evento GED | Día exacto GED | Primera / última fecha de fuente | Best | Cambia clase con supresión unitaria |
|---|---|---|---|---:|---|
| **Azerbaiyán 2021 (GWNO 373)** | **427299** | 17/06/2021 | 06/06/2021 (una fuente) | 1 | No |
| **Togo 2022 (GWNO 461)** | **440185** | 11/05/2022 | 05/05–26/05/2022 (8 fuentes) | **23** | **Sí** |

**Importante:** que uno o varios artículos citados antecedan a la fecha de un evento no demuestra que UCDP codificara mal la fecha. Un codificador puede consultar una publicación previa como contexto de actores u operaciones, y noticias posteriores para obtener el día real. El caso Togo es prioritario para cotejar las **ocho referencias bibliográficas individuales y los hechos descritos**, porque su best=23 podría afectar al indicador país-año 34→11 si se justificara una exclusión completa, que **no está justificada** por estas métricas.

### Controles de interpretación

Los dos registros de Uganda **460859** y **462156**, previamente revisados en la PR #140, presentaron **discordancias explícitas de un día entre el texto público del evento y la fecha exacta GED**, una prueba diferente de los retrasos normales de publicación. En el censo son controles preexistentes: **no** se han redescubierto ni clasificado como dos errores independientes nuevos.

En total, solo **uno de los 13 registros matemáticamente pivote** tiene la primera fecha conocida de fuente anterior al evento codificado; los otros doce no se declaran correctos solo por la cronología de sus publicaciones.

**Consecuencia científica:** antes de atribuir fragilidad a GEO por errores de fecha hay que pasar del *metadata screening* a la **adjudicación de cada fuente original**. El orden lógico de la siguiente auditoría es **Togo GED 440185**, luego Azerbaiyán GED 427299; ambos serán evaluados sin reetiquetar UCDP, sin nuevas emisiones GEO y sin cambios en Brier.
