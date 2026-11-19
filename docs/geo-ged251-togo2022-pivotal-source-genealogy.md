# PSICOHISTORIA · Togo 2022: primer evento pivotal y noticia anterior al hecho

**Estudio preregistrado 19/11/2026** y continuación del [censo de fechas de publicaciones GED25.1, PR #141](geo-ged251-near25-source-publication-lag-census.md).

El censo de 118 filas detectó una entrada Togo GED25.1 **440185**, fecha exacta codificada **11/05/2022**, con **best=23**, dentro de un total país-año de **34 fallecidos** de violencia estatal (tipo 1). Entre sus **ocho referencias de prensa** hay una publicada **el 05/05**, anterior al hecho, y otras hasta el **26/05**. Esta diferencia inicial **no es por sí misma un error**: una referencia anterior puede aportar contexto o información sobre los actores.

## Diseño anterior al examen de las ocho referencias

1. Fijar ID 440185, país GWNO 461, año 2022, 23 fallecidos, date_prec=1, primer source_date 05/05, último 26/05, ocho fuentes y 34 fallecidos en el total anual según el JSON de la PR #141.
2. Releer el ZIP oficial UCDP GED25.1 **SHA-256 e256f1fb20a579d8b2f910e5bae212f486d3002adaa2e4359ace740c737da05d**, extraer sin ambigüedades las ocho referencias bibliográficas originalizadas y la evolución de la publicación. Validar que fuente y fecha coinciden en la misma posición del CSV separado por punto y coma y que las estimaciones de fallecidos por cada parte suman `best=23`.
3. Contrastar independientemente del listado GED el **comunicado togolés del 11/05**, la declaración de la **Unión Africana del 12/05**, y el anuncio de **alrededor de 15 atacantes** formulado por el ministro del Interior y publicado el 19/05; no contar a AU, ONU o agencia de prensa como testigos independientes de cuerpos sin prueba documental de esa independencia.
4. La suma **8 miembros de fuerzas armadas + aproximadamente 15 presuntos atacantes = 23** es una posible explicación aritmética de `best`, **no un recuento forense** ni evidencia de que una fuente del 05/05 conociera el ataque futuro.
5. Separar lo sustentado: ocurrencia del ataque y ocho fallecidos oficiales de la fuerza militar; respecto a las quince bajas de atacantes posteriores se requiere evidencia independiente y relación de personas o combates. Ninguna de las dos cifras debe modificarse basándose solo en fecha editorial.
6. Una hipotética eliminación total de GED 440185 restaría 23 al total anual (34→11), pero **solo sería pertinente si el evento entero fuese falso**, algo contrario a la existencia del ataque confirmada por documentos contemporáneos. Una revisión que afectase exclusivamente a los presuntos atacantes requeriría otro escenario y justificación independiente. No se recodificará la serie ni se reemitirá GEO.

### Fuentes primarias e institucionales usadas

- [Comunicado oficial de Togo 11/05/2022, original PDF firmado](https://securite.gouv.tg/wp-content/uploads/2022/05/COMMUNIQUE-DU-GOUVERNEMENT.pdf): ataque en Kpékpakandi durante madrugada 10–11/05, **ocho integrantes de seguridad muertos y trece heridos**.
- [Unión Africana 12/05](https://au.int/en/pressreleases/20220512/auc-chairperson-statement-terrorist-attack-togo): confirma la condena de la agresión y comunica el mismo **8 y 13**.
- [Portal oficial de Togo, 19/05](https://www.republiquetogolaise.tg/securite/1905-6907-attaque-terroriste-de-kpekpakandi-une-quinzaine-de-morts-parmi-les-assaillants): cita estimación ministerial de **aproximadamente quince presuntos atacantes muertos**, alegadamente enterrados en territorio vecino.
- [Africanews / AFP, 19/05](https://www.africanews.com/2022/05/19/togo-s-government-alleges-15-assailants-killed-during-last-week-s-attack/): reelabora el **mismo comunicado ministerial**, sin investigaciones de cadáveres independientes.
- [Informe S/2022/521 de Naciones Unidas](https://unowas.unmissions.org/sites/default/files/s_2022_521-en.pdf): reseña en retrospectiva el ataque de mayo y los **ocho soldados muertos**, no identifica por separado a los supuestos quince atacantes.

**Riesgo de dependencia:** múltiples publicaciones pueden proceder exactamente de una de dos comunicaciones del Gobierno de Togo, y publicar en distintos días no las convierte en cinco mediciones independientes. El documento del 05/05 se revisará por su referencia exacta de UCDP antes de imputar un error cronológico.

## Reproducción y reglas

Los resultados computacionales quedan en [JSON GED oficial](../data/geo-ged251-togo2022-440185-source-genealogy.json) y las anotaciones externas en [revisión pública](../data/geo-ged251-togo2022-440185-public-review.json).

- `python3 -B -m unittest discover -s scripts -p 'test_audit_geo_togo2022_440185_source_genealogy.py' -v`
- `python3 -B scripts/audit_geo_togo2022_440185_source_genealogy.py --check-report`
- `python3 -B scripts/audit_public.py`

**Límites:** fuentes públicas no archivadas por SHA; datos UCDP históricos revisados desde una edición **publicada en 2025**, no perspectiva real-time de 2022. No existe prueba de error por parte de UCDP ni verificación independiente de quince presuntos insurgentes. Sin modificaciones del target, probabilidades emitidas o métricas Brier.
