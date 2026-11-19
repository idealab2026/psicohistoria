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
