# PSICOHISTORIA · Uganda 2022: elegibilidad de muertes en la díada Gobierno–IS

**Estudio 19/11/2026.** Continuación específica de la [PR #138](https://github.com/idealab2026/psicohistoria/pull/138), que distinguió dos fallecimientos en Kampala pero no certificó la adscripción de las muertes al conflicto Gobierno de Uganda–IS (díada GED25.1 **16938**).

## Pregunta y distinción fundamental

Los registros GED25.1 **444764** (Makindye, 05/06/2022, best=1) y **444765** (Old Kampala, 02/06/2022, best=1) tienen muertes y días distintos. El total observado de violencia estatal de Uganda en 2022 es **25**, exactamente el umbral del indicador binario usado en GEO. Esto los hace *matemáticamente pivote* si se excluyeran del total.

**Sin embargo:** un policía que mata a un sospechoso durante una investigación criminal no es necesariamente una muerte de combate contra una organización insurgente. La [definición oficial de UCDP](https://www.uu.se/en/department/peace-and-conflict-research/research/ucdp/ucdp-definitions) exige violencia armada entre partes de un conflicto que disputan el gobierno o territorio. La [metodología de GED](https://www.uu.se/en/department/peace-and-conflict-research/research/ucdp/ucdp-methodology.html) exige un episodio letal ligado a actores organizados y examina expresamente intereses y dependencia de las fuentes.

El criterio de **25 muertes por año y díada** para considerar activo un conflicto no equivale conceptualmente al **indicador agregado país-año** sum(best) ≥25 utilizado por GEO. Además, GED puede incluir episodios de un año con menos de 25 muertes si una díada alcanzó el umbral en otro año. No inferir que eliminar una muerte demostraría una recodificación obligatoria de toda la historia de una díada.

## Primera revisión pública de genealogía de las fuentes

| Publicación | Fecha | Raíz informativa identificada | Contribución y límite |
|---|---|---|---|
| [Policía de Uganda, comunicado original](https://upf.go.ug/dci-arrests-24-suspects-involved-in-terror-financing-two-others-killed/) | 24/06/2022 | Portavoz policial Fred Enanga | Atribuye dos muertes diferentes a una operación y a un robo frustrado; afirma financiación de ADF. **Actor involucrado, no testigo independiente** |
| [SoftPower News](https://softpower.ug/24-suspects-arrested-for-funding-adf-terrorist-activities-in-uganda-and-drc/) | 24/06/2022 | Mismo comunicado policial | Republica atribuciones del portavoz, sin prueba individual de condición bélica |
| [Uganda Radio Network, junio](https://ugandaradionetwork.net/story/two-killed-24-arrested-in-adf-terror-related-activities-) | 24/06/2022 | Mismo portavoz | Contrasta la narración informativa, no añade un origen independiente de las dos muertes |
| [Daily Express](https://dailyexpress.co.ug/2022/06/25/two-killed-24-arrested-on-allegations-of-terror-financing/) | 25/06/2022 | Mismo portavoz | Describe circunstancias de Makindye y Old Kampala, atribuidas a la Policía |
| [The Independent, entrevista posterior](https://www.independent.co.ug/investigators-cite-soldiers-policemen-as-collaborators-in-kampala-violent-crimes/) | 09/09/2022 | **Otro** responsable de seguridad ugandés, no civil independiente | Afirma que los agentes localizaron al fallecido de Makindye en su domicilio y lo mataron allí; no acredita que fuera combatiente IS |
| [The Observer, relato atribuido a URN](https://observer.ug/news/investigators-cite-soldiers-policemen-as-collaborators-in-kampala-violent-crimes/) | 11/09/2022 | Mismo relato atribuido al segundo oficial | No puede tratarse como un tercer testigo independiente |

**Resultado de la genealogía:** cuatro publicaciones de junio comparten como raíz un único comunicado; dos publicaciones posteriores utilizan un **segundo informante también de las fuerzas de seguridad**. En las páginas revisadas no se ha identificado ningún testimonio *externo a las fuerzas de seguridad* sobre afiliación individual al grupo insurgente ni combates entre ambas partes. No se afirma que tal testigo no exista.

### Análisis por acontecimiento

**GED 444765 · 2 de junio · Old Kampala.** La Policía describe un robo a un comerciante frustrado por los agentes. No presenta evidencia individual independientemente corroborada de participación directa del fallecido en enfrentamiento por control gubernamental/territorial, ni un intercambio armado con una de las partes del conflicto. Que integrantes *de una red criminal más amplia* presuntamente recaudaran fondos para ADF no establece la condición de combatiente de esta persona, ni convierte automáticamente el robo en violencia estatal de combate.

**GED 444764 · 5 de junio · Makindye.** La fuente policial describe una intervención violenta y supuesta resistencia. El relato de septiembre cita a otro mando que habla de localización del sospechoso y muerte en el lugar. Son **relatos de dos agentes de la misma institución**, que no permiten confirmar por sí solos si hubo resistencia armada, qué ocurrió exactamente ni la relación personal del fallecido con un objetivo militar o político. No se demuestra una falsedad policial ni un error de UCDP a partir de la diferencia retórica.

### Lo que falta para decidir

Una revisión con evidencias verdaderamente contrastables necesitaría (i) pruebas específicas de pertenencia a la parte combatiente pertinente y no mera asociación policial a financiación, (ii) testimonio o material independiente sobre uso de fuerza **entre partes del conflicto** en cada muerte y (iii) justificación del nexo con la incompatibilidad por gobierno o territorio. Solo después de eso puede resolverse la elegibilidad. No hay suficientes pruebas para establecer una etiqueta alternativa verdadera.

## Prueba cuantitativa reproducible

El script lee el **ZIP completo GED25.1** fijado por SHA-256, enumera **todas** las filas de Uganda de tipo 1 en 2022, reconstruye sus díadas y comprueba contra el total **25** del estudio anterior. Después enumera escenarios **hipotéticos** y no implementados de exclusión: 0 registros excluidos → 25 (activo), excluir 444764 → 24, excluir 444765 → 24 y excluir ambos → 23. No son estimaciones probabilísticas de la legitimidad de ninguna exclusión.

Las agrupaciones anuales que publica el script proceden de UCDP; no son un conjunto de fuentes externas independientes. El [artículo científico UCDP sobre violencia organizada en 2022](https://journals.sagepub.com/doi/abs/10.1177/00223433231185169) también documenta Uganda–IS (2022) con estimación best de 25, pero **es una publicación derivada de UCDP**, por lo que no cuenta como comprobación de las dos muertes.

La revisión editorial está en [JSON de genealogía](../data/geo-ged251-uganda-2022-eligibility-source-genealogy.json). El [resultado reproducido](../data/geo-ged251-uganda-2022-eligibility-dyad-stress.json) se contrasta contra el ZIP oficial y el informe #138. Los enlaces remotos se revisaron en HTML, pero **no se archivó ni hasheó su contenido**, solo las anotaciones Git y la fuente oficial GED.

### Reproducción y garantías

- python3 -B -m unittest discover -s scripts -p 'test_audit_geo_uganda2022_statebased_eligibility.py' -v
- python3 -B scripts/audit_geo_uganda2022_statebased_eligibility.py --check-report
- python3 -B scripts/audit_public.py

**Prohibiciones expresas:** ningún evento UCDP eliminado, ninguna probabilidad GEO2027/GEO2028 reemitida y ninguna mejora de Brier declarada. El hallazgo es una **cuestión de elegibilidad documental aún irresuelta**, no una demostración de error del conjunto de datos.
