# PSICOHISTORIA · Uganda 2022: reconciliación de fuentes y eventos de diciembre

**Diseño preregistrado 19/11/2026 antes de examinar las citas bibliográficas GED de diciembre.** Continuación de la [auditoría #139](geo-ged251-uganda-2022-statebased-eligibility.md).

## Pregunta de investigación

¿Los 23 fallecidos estatales asignados por UCDP GED25.1 a diciembre de Uganda 2022 están distribuidos en episodios independientes y correctamente atribuidos a la díada Gobierno de Uganda–IS? ¿Puede su evidencia distinguir los hechos bélicos explícitos de diciembre de las dos muertes policiales de junio, cuya elegibilidad sigue irresuelta?

No puede inferirse una respuesta afirmativa simplemente por el hecho de que GED asigne los seis eventos a la misma díada. Esta fase estudia metadatos, fechas, fuentes originales y dependencias. **No reescribe el total ni propone excluir ninguna víctima.**

## Datos y selección cerrados

La PR #139 congeló la díada 16938, sus seis filas y su suma best de 25 muertes. Los cuatro registros de diciembre tienen IDs **460796 (best=19, 12–13/12)**, **460859 (best=2, 21/12)**, **460862 (best=0, 13–27/12)** y **462156 (best=2, 19/12)**. El total de diciembre es 23 en UCDP GED25.1 (ZIP oficial SHA-256 e256f1fb20a579d8b2f910e5bae212f486d3002adaa2e4359ace740c737da05d).

La selección **precede** al examen del contenido bibliográfico individual de esos cuatro eventos.

## Protocolo

1. Reproducir la edición oficial SHA-256 y exigir identidad de seis eventos, díada, país, año, fechas y número de muertos del análisis previo.
2. Leer por cada entrada de diciembre: fecha inicial/final y precisión, localidad y precisión geográfica, claridad, estimaciones low/best/high, actores, díada, fuente original, número de fuentes y referencias en formato GED25.1 CSV entrecomillado separado por punto y coma.
3. Comparar las seis parejas posibles dentro de diciembre por distancia, solapamiento temporal, fuente original y huellas exactas de referencias. **Un mismo titular o comunicado no demuestra corroboración independiente ni duplicación**.
4. Buscar informes contemporáneos y, de forma claramente diferenciada, retrospectivas de instituciones independientes. Identificar si corroboran choque armado entre los bandos o únicamente citan versiones de las fuerzas armadas. Priorizar la acción en Ntoroko del 12–13 de diciembre y posteriores operaciones de Wakiso/Ntoroko.
5. No equiparar balances **acumulados** posteriores (11, 15, 17, 20, 26) con víctimas diferentes sin una reconciliación por fecha y persona. Las cifras sobre combatientes abatidos, civiles y detenidos deben mantenerse separadas, nunca sumarse por simple yuxtaposición.
6. La fila 460862 con **best=0** no es prueba de que no hubiera violencia, ni permite decir que sus estimaciones low/high también sean cero antes de observar el registro.
7. Mantener los dos sucesos policiales de junio en **elegibilidad no resuelta**, sin convertir la evidencia más sólida de diciembre en verificación retrospectiva automática de junio.
8. Mantener inmutables los datos oficiales y las predicciones emitidas GEO2027/GEO2028; no declarar validación de skill ni cambios reales del Brier.

La reproducción oficial generará un artefacto JSON con la trazabilidad individual y un análisis de solapamientos **exploratorio, no una adjudicación de víctimas**. El registro de fuentes adicionales se añadirá solo tras revisar las páginas originales.

## Fuentes contextuales preliminares (no utilizadas aún para atribuir episodios GED concretos)

- [UPDF: informe militar de Operación Shujaa a 15/12/2022](https://www.updf.go.ug/press-release/general-security-update-on-updf-operations/).
- [The EastAfrican, 14/12/2022: versiones enfrentadas sobre víctimas civiles](https://www.theeastafrican.co.ke/tea/news/east-africa/ugandan-troops-kill-15-adf-rebels-4053852).
- [Daily Monitor, 20/12/2022: dos muertos en un operativo de Wakiso](https://www.monitor.co.ug/uganda/news/national/how-security-hunted-down-suspected-adf-rebels-in-wakiso-4060832).
- [Panel de Expertos de la ONU, informe S/2023/990, Anexo 10](https://digitallibrary.un.org/record/4032027): documento **retrospectivo de 2023**, no noticia disponible en diciembre de 2022.

**Límite de fuente:** prensa que replica cifras del UPDF no equivale a verificación independiente de cuerpos; una investigación posterior de la ONU puede aportar fuentes diferentes, pero es retrospectiva y puede tratar una parte distinta de los episodios. La fuente primaria del participante tiene un potencial conflicto de interés.

Ejecución: python3 -B -m unittest discover -s scripts -p 'test_audit_geo_uganda2022_december_source_families.py' -v; python3 -B scripts/audit_geo_uganda2022_december_source_families.py --check-report; python3 -B scripts/audit_public.py.

## Resultados oficiales GED25.1 y contraste documental completado

Se descargó de nuevo el ZIP oficial, con **SHA-256 válido**, y se reprodujeron las cuatro filas preseleccionadas, sus metadatos completos y su dependencia bibliográfica. La suma **low=23, best=23, high=26** en diciembre, más los dos best=1 de junio, reproduce **low=25, best=25, high=28** en la díada anual. No existe ninguna verificación independiente de que los 23 fallecidos GED correspondan a 23 personas individualmente identificadas.

| GED | Fechas según GED y precisión temporal | Low / best / high | Observación geográfica UCDP | Resultado documental |
|---|---|---|---|---|
| **460796** | 12–13/12; date_prec=2 | **19 / 19 / 19** | Rwebisengo, Ntoroko (where_prec=2) | Combate entre UPDF y ADF respaldado cualitativamente; **19 muertos no verificados por relación nominal independiente** |
| **460859** | **21/12; date_prec=1** | **2 / 2 / 2** | Bweramule, Ntoroko (where_prec=2) | Uganda Radio Network, publicada el miércoles 21, dice que **ocurrió el martes 20**: desfase aparente de un día |
| **460862** | 13–27/12; date_prec=4 | **0 / 0 / 3** | Localización imprecisa en Ntoroko (where_prec=4) | Fuente bibliográfica habla de **26 muertos acumulados durante el mes**; no implica 26 nuevas víctimas ni tres confirmadas adicionales |
| **462156** | **19/12; date_prec=1** | **2 / 2 / 2** | Kito, Matugga/Wakiso (where_prec=1) | Comunicado original de la Policía **del 19 de diciembre** sitúa la operación en **el 18**; Daily Monitor se refiere igualmente al domingo anterior |

Las cuatro fechas y los intervalos low/best/high son **datos de UCDP, no adjudicaciones propias**. En 460859 y 462156 UCDP indica `date_prec=1` (día preciso), mientras las dos fuentes contemporáneas consultadas describen un día anterior al registrado. Por tanto **hay dos posibles desfases de un día entre fecha del hecho y fecha de publicación**, con respaldo textual; no se cambia la fuente oficial porque faltan la cronología y las decisiones completas del codificador.

### Ntoroko: distintas fuentes para el enfrentamiento, no para toda la cifra de muertos

El [informe militar UPDF, estado a 15 de diciembre](https://www.updf.go.ug/press-release/general-security-update-on-updf-operations/) atribuye **20 combatientes** muertos al enfrentamiento del 13 de diciembre. [Daily Monitor, 14 de diciembre](https://www.monitor.co.ug/uganda/news/national/armed-cross-border-attack-leaves-19-dead-4054508) recoge el balance informado por el comandante: **17 presuntos ADF, un soldado y un civil**; el diario advierte que no pudo comprobar las muertes de combatientes al no acceder al frente. [The EastAfrican](https://www.theeastafrican.co.ke/tea/news/east-africa/ugandan-troops-kill-15-adf-rebels-4053852) recoge además divergencias de líderes locales sobre víctimas civiles y titulares de diferentes fases del operativo.

La síntesis de [International Crisis Group publicada en enero de 2023](https://crisisgroup-staging.sbx.so/crisiswatch/january-alerts-and-december-trends-2022) atribuye **17 muertos entre los agresores y dos civiles muertos**, misma suma 19 pero distinta composición de víctimas que el comunicado anterior. No hay aquí un registro independiente que pruebe todas las identidades y categorías. El supuesto de que 19=17+1+1 queda identificado como **una descomposición compatible con un reporte contemporáneo**, no como verdad pericial certificada.

El **Panel de Expertos de la ONU** ([informe S/2023/990 de 30/12/2023, anexo 10, páginas impresas 39–40](https://documents.un.org/doc/undoc/gen/n23/364/37/pdf/n2336437.pdf)) confirmó mediante su investigación posterior que hubo incursión de combatientes ADF en **Ntoroko el 13/12/2022**, con enfrentamiento armado contra UPDF; identifica al menos dos mandos muertos en combate. **No certifica el censo íntegro de 19**. Su mapa contiene la inscripción «13 December 2023» para Ntoroko mientras el relato del propio anexo dice expresamente **2022**: debe tratarse como discordancia interna de rotulación, nunca como un segundo enfrentamiento no comprobado.

### Las otras dos muertes en Ntoroko: separar fecha del hecho y fecha del diario

La [noticia original de Uganda Radio Network fechada 21/12/2022](https://ugandaradionetwork.net/story/two-adf-rebels-killed-in-ntoroko-) relata que fueron abatidos el **martes 20** cuando trataban de regresar hacia el Congo. La [republicación de The Independent](https://www.independent.co.ug/two-adf-rebels-killed-in-ntoroko/) declara expresamente procedencia URN y **no constituye un segundo testigo**. El oficial provincial citado es también una fuente del Estado. Se describe un enfrentamiento distinto y posterior al del 13 de diciembre, no 19+2 muertos en la misma fecha; la exactitud del **21** indicado en GED requiere aclaración.

### Wakiso: posible error de fecha y elegibilidad de la operación policial

El [comunicado de Uganda Police Force del 19/12/2022](https://upf.go.ug/fsu-ci-task-teams-counter-terrorists-and-dismantles-two-terror-cells-in-maganjo-and-matugga/) afirma explícitamente que hubo un operativo en **Matugga el 18 de diciembre** que terminó con dos presuntos miembros ADF muertos, armas incautadas y un supuesto intercambio de disparos. [Daily Monitor del 20/12](https://www.monitor.co.ug/uganda/news/national/how-security-hunted-down-suspected-adf-rebels-in-wakiso-4060832) dice igualmente «domingo» y recoge a vecinos que describen múltiples disparos policiales antes de entrar en la habitación.

La presencia de reporteros y testimonios vecinales aumenta el contexto independiente sobre la **operación**; **no prueba quién abrió fuego primero ni la filiación militar de los fallecidos**. El relato policial atribuye antecedentes de ataques a puestos de policía; esa atribución puede ser importante, pero exigiría corroboración independiente para decidir si todas las muertes constituyeron un choque armado entre partes enfrentadas por una incompatibilidad político-territorial.

### Registro 460862: el mayor riesgo de error automático de agregación

La fila GED **460862**, asociada a una publicación del 27/12 sobre un balance acumulado **26** en Ntoroko, contiene **best=0, high=3** y ventana amplia. No corresponde añadir 26 muertes nuevas ni tratar el extremo superior como tres bajas confirmadas. En la base oficial, un investigador que sumara titular y fallecidos anteriores estaría potencialmente **contando dos veces** relatos solapados; eso no significa que GED lo haga, porque la propia edición asigna best=0 a ese registro.

### Hallazgo de genealogía bibliográfica

La entrada **460796** tiene ocho fragmentos bibliográficos GED, pero **uno de los artículos Reuters aparece dos veces**, por lo que solo hay **siete fragmentos exactos diferentes**. Entre las seis parejas de entradas de diciembre, **solo 460796 y 460859 comparten una cita exacta**, la noticia de Daily Monitor de 21 de diciembre. No debe interpretarse como dos conteos forenses de víctimas.

El protocolo estructurado y sus nueve publicaciones externas están en [la revisión documental JSON](../data/geo-ged251-uganda-2022-december-public-source-review.json), enlazada con [el reporte oficial congelado](../data/geo-ged251-uganda-2022-december-source-families.json). Los controles obligan a identificar diferencias entre `date_prec`, fecha atribuida a un hecho y fecha de la fuente, e impiden reclasificar un evento o certificar un censo individual de víctimas sin evidencia.

**Resultado general:** el enfrentamiento de Ntoroko sí tiene una base cualitativa externa más sólida, pero ello **no resuelve** la elegibilidad de las muertes de junio en Kampala ni la de los operativos policiales de Wakiso. El problema científico pasa a ser doble: **desfases de fecha** y **elegibilidad estatal por episodio**, manteniendo intactas las predicciones GEO.
