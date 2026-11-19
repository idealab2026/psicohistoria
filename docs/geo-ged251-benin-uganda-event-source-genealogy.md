# PSICOHISTORIA · Benín y Uganda 2022: trazabilidad de cuatro eventos decisivos

**Diseño inicial 19/11/2026** (tras PR #137, antes de abrir las fuentes bibliográficas de los cuatro registros). Auditoría documental y de dependencia para dos parejas seleccionadas por impacto matemático en el umbral de 25 muertes de violencia estatal por país/año.

## Cohorte y pregunta

La revisión [#137](geo-ged251-near25-countryyear-census.md) fijó **392 país-años**, una banda inclusiva **15–35** muertes estatales GED25.1 y, antes de observar noticias individuales, estos pares candidatos:

| País-año | Total GED25.1 tipo 1 | Eventos seleccionados | Mortandad GED best por evento | Razón de prioridad |
|---|---:|---|---|---|
| Benín 2022 | 30 | 431254 / 431259 | 8 / 1 | Borrar *hipotéticamente* el primero da 22 |
| Uganda 2022 | 25 | 444764 / 444765 | 1 / 1 | Borrar *hipotéticamente* cualquiera da 24 |

Ambas parejas tienen coordenadas idénticas en el estudio anterior, pero **coincidencia geográfica no significa mismo incidente, misma víctima ni error**.

## Protocolo conservador

1. Volver a verificar SHA-256 del ZIP oficial UCDP GED25.1. Exigir identidad de cuatro IDs de evento, país, año, tipo de violencia y muertes best; abortar ante desviaciones.
2. Leer directamente los campos originales date_start, date_end, date_prec, where_prec, where_coordinates, where_description, event_clarity, dyad_name, side_a, side_b, source_original, number_of_sources y metadatos bibliográficos source_article, source_date, source_headline y source_office.
3. Establecer si UCDP reutiliza referencias bibliográficas entre los dos eventos. Conservar huellas SHA-256 de citas y un extracto corto de la referencia (no textos periodísticos). Distinguir noticia citada, fuente original alegada y **verificación independiente**.
4. Diferenciar fecha exacta y ventana incierta, y precisión espacial según [codebook oficial GED25.1](https://ucdp.uu.se/downloads/ged/ged251.pdf). where_prec=2 solo garantiza un margen aproximado de hasta 25 km; dos coordenadas idénticas podrían ocultar enfrentamientos diferentes. Un evento de claridad 2 puede agregar varios choques según codificación UCDP.
5. Buscar en fuentes públicas originales los episodios, establecer si los relatos identifican **fechas y víctimas distintas**, y clasificar cada pareja únicamente como _resuelta-distinta_, _solapamiento-verificado_ o _indeterminada_. La coincidencia en actor, díada, día o cifra no basta para declarar duplicación. Si falta material contrastable, mantener el estado de indeterminación.
6. No reescribir UCDP, emitir nuevas probabilidades GEO2027/2028 ni declarar cambio real en Brier. La sensibilidad 30→22 y 25→24 es **hipotética**, nunca una corrección certificada.

La evidencia de fuentes se recopila exclusivamente desde referencias públicas. No se incluyen nombres de particulares ni fuentes de la cuenta personal del investigador. Este protocolo está fijado en Git antes de analizar los metadatos de las cuatro entradas.

## Interpretación y reproducibilidad

La [metodología UCDP de claridad de evento](https://ucdp.uu.se/downloads/ged/ged251.pdf) distingue episodios claramente identificados (event_clarity=1) de agregados de varios enfrentamientos que el codificador no puede separar (=2). Esto es relevante para distinguir eventuales solapamientos **de la misma narración** de episodios que ocurren a unos días de distancia.

Ejecución:

- python3 -B -m unittest discover -s scripts -p 'test_audit_geo_ged251_benin_uganda_source_pair.py' -v
- python3 -B scripts/audit_geo_ged251_benin_uganda_source_pair.py --check-report
- python3 -B scripts/audit_public.py

El protocolo se registró antes de inspeccionar las cuatro entradas. **Se ha completado la reproducción oficial SHA y congelado el JSON; CI exige ahora repetición exacta.** Las noticias originales disponibles se han leído y comparado; no se han archivado por SHA ni hay verificación forense independiente de todas las víctimas o de su adscripción al conflicto.

## Resultados de las cuatro filas oficiales y revisión de fuentes públicas

**Archivo base:** UCDP GED25.1 oficial, con ZIP SHA-256 comprobado; cuatro IDs de evento incluidos en el estudio #137. Las referencias bibliográficas GED25.1 están codificadas en un CSV con fragmentos entrecomillados **separados por punto y coma**. No deben dividirse mediante el separador de otras variantes UCDP: esa confusión subcontaba el solapamiento de fuentes. El lector se corrigió y se añadieron pruebas adversariales de títulos que contienen punto y coma.

| Dimensión | Benín: GED 431254 / 431259 | Uganda: GED 444764 / 444765 |
|---|---|---|
| Fechas GED | **08/02 y 10/02/2022** | **05/06 y 02/06/2022** |
| Muertes GED best, respectivamente | **8 / 1** | **1 / 1** |
| Intervalo GED low–high | 8–8 / 1–1 | 1–1 / 1–1 |
| Claridad GED | 1 / 1 | 1 / 1 |
| Precisión temporal GED | 1 / 1 | 1 / 1 |
| Precisión espacial GED | 2 / 2 | 1 / 1 |
| Díada UCDP | Gobierno de Benín – JNIM, misma | Gobierno de Uganda – IS, misma |
| Citas bibliográficas GED en cada registro | 9 / 4 | 2 / 2 |
| **Referencias idénticas compartidas** | **4** | **2** |
| Fuente original identificada en GED | African Parks / autoridades de Benín | Portavoz de la Policía ugandesa / mismo origen |
| Coordenadas registradas | Idénticas | Idénticas |
| Lugares descritos | Parque W, dos fechas | Makindye y Old Kampala, zonas distintas |

### Benín · Diferencia de incidentes, discrepancia en el balance de muertos

- [African Parks, comunicado inicial 09/02/2022](https://www.africanparks.org/incident-w-national-park) informa de una emboscada sufrida el **08/02**. Los datos iniciales son preliminares.
- [African Parks, actualización 11/02/2022](https://www.africanparks.org/update-incidents-w-national-park-benin) **distingue** el ataque complejo del día 8 de un nuevo impacto por artefacto explosivo el **10/02**, que causó una muerte adicional. Sin embargo, su desglose global para los dos días suma **ocho muertes**.
- [UNESCO, 14/02/2022](https://whc.unesco.org/en/news/2404/) confirma que se comunicaron **dos ataques en fechas distintas**, pero no ofrece un listado forense nuevo de víctimas.
- [International Crisis Group, retrospectiva de febrero 2022](https://crisisgroup-staging.sbx.so/crisiswatch/march-alerts-and-february-trends-2022) resume **ocho muertes el día 8 y una el día 10**: nueve en total, cifra coherente con la suma GED 8+1 pero diferente del total de ocho que presenta African Parks en su actualización.

**Decisión de episodio:** hay evidencia pública contemporánea de **ataques diferentes** (8 y 10 de febrero). Un mismo municipio, una misma díada y cuatro citas compartidas **no justifican fusionarlos**.

**Cuestión abierta:** el **balance agregado ocho frente a nueve** de ambas publicaciones **no está reconciliado**. No se sabe si responde a actualización incompleta, distinta composición de las víctimas u otra diferencia. No se dispone de listas nominales independientes que permitan juzgar la cifra correcta. Una hipotética corrección de una única muerte llevaría 30→29 en el total anual, **sin cruzar 25**; pero esto es solo una ilustración aritmética, no una corrección recomendada ni demostrada.

### Uganda · Dos fallecidos identificados en una misma nota policial, no dos fuentes independientes

El [comunicado oficial de la Policía ugandesa del 24/06/2022](https://upf.go.ug/dci-arrests-24-suspects-involved-in-terror-financing-two-others-killed/) explica que un sospechoso falleció en **Old Kampala el 02/06** durante un robo frustrado y **otra persona** murió en **Makindye el 05/06** durante una operación policial. Son muertes distintas en fechas y lugares distintos, aunque GED asigne las mismas coordenadas de **Kampala city**. El [artículo de Nile Post del 24/06](https://nilepost.co.ug/news/137037/police-say-two-killed-24-arrested-in-operations-targeting-suspected-adf-funders-in-kampala) transmite declaraciones del mismo portavoz y **no** se cuenta como investigación independiente.

**Decisión de episodio:** los relatos de la fuente original identifican **dos personas y dos acciones policiales diferenciadas**; fusionar GED 444764 con GED 444765 implicaría borrar arbitrariamente una muerte ya distinguida por el propio relato.

**Problema abierto más importante:** la Policía sostiene que los sospechosos participaban en una red de financiación de las ADF. Eso **no demuestra por sí mismo** la afiliación bélica de cada fallecido, ni que ambos incidentes constituyan violencia organizada *state-based* entre el Gobierno e IS a efectos de la metodología UCDP. En particular, el segundo caso aparece descrito como una actuación ante un robo. Es necesario contrastar el **criterio de elegibilidad del actor y del hecho letal**, no la identidad de dos muertos distintos. No se recodifica ninguna fila por esta hipótesis.

### Alcance de la evidencia

Las páginas HTML han sido leídas en la investigación, y sus URL, fechas y afirmaciones están anotadas en [la revisión pública estructurada](../data/geo-ged251-benin-uganda-public-firstparty-review.json). **No se han archivado ni autenticado sus bytes remotos por SHA-256.** Un comunicado de la entidad implicada y su republicación periodística no son verificaciones forenses independientes. El informe computacional [JSON GED25.1](../data/geo-ged251-benin-uganda-2022-source-pair-audit.json) conserva únicamente metadatos, huellas y referencias breves, no el texto integral de las noticias.

**Conclusión:** las coincidencias espaciales de ambos pares son **falsos positivos para una búsqueda ingenua de duplicados**; los riesgos que permanecen son el recuento exacto de Benín y, sobre todo, la elegibilidad de la violencia estatal de Uganda. La reducción contrafactual 30→22 o 25→24 no constituye una corrección válida sin nuevos hechos. En ningún caso se han modificado las etiquetas GED ni los pronósticos prospectivos GEO.
