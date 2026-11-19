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
