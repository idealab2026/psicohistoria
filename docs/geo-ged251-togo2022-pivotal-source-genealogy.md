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

## Resultado efectivo de las ocho referencias GED25.1

**Reproducción SHA-256 del ZIP UCDP 25.1 y contraste con el comunicado firmado de 11 de mayo.** La codificación GED 440185 es explícita:

| Medición | Valor |
|---|---:|
| Muertes de militares, `deaths_a` | **8** |
| Muertes de atacantes JNIM, `deaths_b` | **15** |
| Muertes civiles / desconocidos | **0 / 0** |
| Estimación UCDP **low** | **8** |
| Estimación UCDP **best** | **23** |
| Estimación UCDP **high** | **23** |
| Año país Togo, total estatal best | **34** |
| Si solo esta fila se evalúa en low=8 y todas las demás siguen en best | **19** |

**La incertidumbre sobre las 15 bajas atribuidas a los atacantes es matemáticamente decisiva.** La sustitución *hipotética de una sola estimación* `34 - 23 + 8 = 19` cambia la clase country-year `≥25` de sí a no, **sin borrar el ataque ni a los ocho soldados**. Eso no significa que la estimación low sea la correcta ni que GED contenga un error: low, best y high son alternativas publicadas por la propia UCDP para expresar incertidumbre. El resultado se debe separar de la eliminación completa ficticia `34 - 23 = 11`, ya descartada por la documentación del ataque.

La fuente firmada del **11/05** atribuye ocho muertos a fuerzas togolesas. El [comunicado oficial del 19/05](https://www.republiquetogolaise.tg/securite/1905-6907-attaque-terroriste-de-kpekpakandi-une-quinzaine-de-morts-parmi-les-assaillants) atribuye aproximadamente quince bajas adicionales a los asaltantes, alegando que se enterraron fuera del país; es una información **del mismo Gobierno**, transmitida con posterioridad, y no una identificación forense independiente. La combinación de ambas versiones explica la composición numérica oficial, pero no demuestra la realidad exacta de los quince fallecimientos.

### Qué fuentes históricas recoge UCDP

De las **ocho referencias bibliográficas GED**, se observan:

- Reuters (11/05) y AFP (11/05), sobre **ocho militares muertos**, más un breve registro Twitter (11/05);
- BBC Monitoring (12/05), sobre condena regional;
- AFP (19/05), con **quince atacantes muertos según el ministro**;
- Menastream (26/05), referencia contextual;
- otra entrada Twitter (11/05) **con cadena bibliográfica idéntica** a la anterior (ocho entradas en total, siete cadenas distintas);
- **Africa Research Bulletin (05/05)**, catalogada como `Togo: JNIM claims Attack`, cuya fecha editorial **es seis días anterior al ataque GED del 11/05**.

El encabezado de Africa Research Bulletin con fecha de publicación 05/05 no puede tratarse automáticamente como un reporte contemporáneo del ataque del 11/05: puede ser contexto de otro incidente, una edición con fecha nominal anterior al contenido o un error de metadatos de la fuente. **No se ha recuperado y validado el contenido integral de esa edición**; el estado correcto es *referencia de cronología indeterminada* y **no error del día codificado de GED**.

Aunque las fuentes sean ocho entradas, no existen ocho testimonios independientes: hay una referencia idéntica repetida y varios medios publican cifras proporcionadas por el mismo ministerio. Un aumento de fuentes escritas sin independencia de origen **no aumenta automáticamente la probabilidad de que 15 víctimas estén correctamente contabilizadas**.

### Decisión científica

El registro 440185 **no debe suprimirse ni cambiar de fecha** basándose en la presencia de la cita del 05/05. **Sí merece una auditoría específica de la base probatoria de las quince muertes atribuidas a los atacantes**, por su potencial de cambiar el umbral de 25 en Togo 2022. La investigación debe solicitar, idealmente, listas, informes forenses o recuentos de víctimas independientes, y el criterio de UCDP que llevó a elegir `best=23` en lugar de `low=8`.

En este estudio: **cero correcciones a GED**, **cero reemisiones de GEO2027/GEO2028** y **ninguna mejora de Brier demostrada**. El resultado es una sensibilidad de medición etiquetada e históricamente trazable.

Evidencia reproducible: [JSON de las ocho referencias, campos de muertes y contrafactuales](../data/geo-ged251-togo2022-440185-source-genealogy.json), [genealogía de fuentes públicas](../data/geo-ged251-togo2022-440185-public-review.json).
