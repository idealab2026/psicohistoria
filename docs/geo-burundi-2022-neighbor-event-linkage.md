# PSICOHISTORIA · Burundi 2022: controles negativos para resolver episodios próximos

**Fecha de investigación: 19/11/2026.** Continuación de la auditoría institucional [#133](https://github.com/idealab2026/psicohistoria/pull/133) sobre el episodio UCDP GED25.1 **442626**, Mabayi, Cibitoke, junio de 2022.

## Pregunta científica

¿Está un buscador de noticias confundiendo enfrentamientos del mismo lugar y actores (Mabayi, Kibira, FLN) y convirtiendo las víctimas de **otros episodios** en supuestas verificaciones independientes del **19–21 de junio de 2022**?

La ventana de la fuente original no es exacta: unas publicaciones sitúan el episodio entre **18–20/06** y otras entre **19–21/06**. Para controles negativos, el protocolo utiliza una envolvente inclusiva **18–21/06** y tolerancia temporal de **tres días**. No convierte esa envolvente en una fecha de muerte conocida.

## Cinco comparaciones verificadas en páginas públicas

| Fuente publicada | Episodio descrito y cifra atribuida | Relación con junio | Cautela |
|---|---|---|---|
| [SOS Médias Burundi, 09/05/2022](https://www.sosmediasburundi.org/2022/05/09/cibitoke-trois-rebelles-rwandais-et-un-militaire-burundais-tues-a-mabayi/) | Cuatro cuerpos hallados **08/05**: tres presuntos rebeldes y un militar; Mabayi/Gafumbegeti | **Excluida**: publicada antes del episodio de junio | La fecha del combate no está fijada por la fecha del hallazgo |
| [SOS Médias Burundi, 18/07/2022](https://www.sosmediasburundi.org/2022/07/18/cibitoke-quatre-corps-retrouves-dans-la-reserve-naturelle-de-la-kibira/) | Cuatro cuerpos hallados **17/07**; noticia relaciona enfrentamientos con los días anteriores | **Excluida como informe directo de junio** por distinta ventana de enfrentamientos descritos | El descubrimiento **no prueba** la fecha exacta de muerte ni que no compartan identidades con otros registros |
| [SOS Médias Burundi, 14/10/2022](https://www.sosmediasburundi.org/2022/10/14/cibitoke-plus-de-40-rebelles-rwandais-tues-par-larmee-burundaise/) | **Al menos 42 presuntos rebeldes muertos** durante ofensiva que el medio sitúa desde el **26/09**, además de alegaciones separadas de bajas militares | **Excluida** como enfrentamiento de junio por contexto temporal posterior | No sumar cifras de soldados, rebeldes y días como si fueran recuentos equivalentes |
| [SOS Médias Burundi, 03/12/2022](https://www.sosmediasburundi.org/2022/12/03/cibitoke-neuf-corps-de-rebelles-rwandais-retrouves-dans-la-kibira/) | Nueve cuerpos hallados **02/12**, presuntamente vinculados a enfrentamientos recientes | **Indeterminada la fecha de muerte individual**; NO constituye confirmación directa de junio | La descomposición y falta de identidad impiden afirmar que los individuos sean distintos de los de junio |
| [IWACU, 03/04/2023](https://www.iwacu-burundi.org/mabayi-13-cadavres-extraits-de-la-mine-dor-de-gafumbegeti/) | **13 cadáveres recuperados** de un accidente minero, Mabayi/Gafumbegeti | **Excluida por mecanismo no bélico**, además de fecha | Un nombre de localidad y una cifra no identifican violencia organizada |

El informe de [CrisisWatch, agosto de 2022](https://crisisgroup-staging.sbx.so/crisiswatch/august-alerts-and-july-trends-2022) también recoge cuatro cuerpos encontrados **17/07**. Es otra *publicación*, no se ha demostrado una nueva investigación forense ni una segunda relación identificada de víctimas, por lo que **no** se suma una fuente independiente.

## Resultado reproducible

- **5/5** publicaciones contienen referencias locales capaces de producir una coincidencia ingenua por municipio o paisaje.
- **4/5** se descartan como informes directos del enfrentamiento de junio: publicación anterior, fecha de otro ciclo bélico o mecanismo no bélico.
- **1/5** (hallazgo de diciembre) conserva **incertidumbre sobre la fecha de muerte individual**: no debe codificarse ni como confirmación de junio ni como conjunto probado de personas distintas.
- **0** nuevas verificaciones independientes de los diez fallecidos de junio; **0** listas cruzadas de identidad de víctimas verificadas. Estas cifras no son estimaciones de probabilidad de independencia, ni nuevos resultados predictivos.

**Estimandos separados:** episodio periodístico, fecha de observación de cadáveres, fecha real de fallecimiento, identidad individual y balance de mortalidad del año-país. La coincidencia del lugar no permite sustituir uno por otro. Una noticia posterior con varios cadáveres tampoco permite sumarlos al GED del mes anterior.

## Ejecución y criterios de rechazo

```bash
python3 -B -m unittest discover -s scripts -p 'test_audit_geo_burundi_2022_neighbor_event_linkage.py' -v
python3 -B scripts/audit_geo_burundi_2022_neighbor_event_linkage.py --check-report
python3 -B scripts/audit_public.py
```

El script no accede a internet: compara exclusivamente anotaciones editoriales en `data/geo-burundi-2022-neighbor-event-linkage.json`. Conserva la cadena científica de la auditoría #133, reconstruye las decisiones de clasificación e impone la inmutabilidad de GEO2027/GEO2028. Las URL se han verificado mediante lectura de páginas HTML públicas, pero los **bytes remotos no se han descargado ni archivado con SHA-256**. El historial Git fija las anotaciones, no el estado futuro de las webs. Los informes son **post hoc**, no una evaluación de aciertos prospectivos.

## Implicación para el siguiente estudio

Aplicar estos controles a un muestreo **preespecificado, ciego a la salida del modelo**, de eventos GED de distintos países/años. Medir tasa de fusiones falsas y discrepancias con una revisión humana; **solo entonces** estimar impacto sobre etiquetas país-año y Brier. Este caso único es útil para probar el protocolo, **no** para calcular tasas generales de error de UCDP ni corregir las probabilidades emitidas.
