# UCDP Candidate — Auditoría de revisiones de versiones trimestrales Q2→Q3 (19-11-2026)

**Estado de este protocolo: prerregistrado antes de observar resultados del nuevo contraste. No es un modelo ni una emisión prospectiva.**

## Pregunta predefinida

¿Cuánto cambian los registros provisionales de **enero a junio** de un mismo año cuando se compara el acumulado UCDP Candidate publicado como edición enero–junio (Q2) frente al acumulado enero–septiembre (Q3)?

Realizar el mismo contraste en los años **2024, 2025 y 2026**, usando exclusivamente archivos descargables oficiales de <https://ucdp.uu.se/downloads/olddw.html>, sin reemplazarlos con GED anual. Cada archivo deberá identificarse por URL completa, SHA-256, bytes y número de registros. Q2 y Q3 son dos versiones del **mismo periodo histórico**; no son observaciones independientes y la diferencia de versiones NO es un test predictivo.

## Universo, filtros y controles fijados ex ante

1. Usar seis archivos: `GEDEvent_vYY_01_YY_06.csv` y `GEDEvent_vYY_01_YY_09.csv` para YY = 24, 25 y 26. Comprobar dominio HTTPS y nombre, esquema GED y ausencia de IDs duplicados **dentro** de cada archivo. No concatenar acumulados como si fuesen eventos distintos.
2. El universo a comparar son registros con `date_start >= 1 enero` y `date_end <= 30 junio` del mismo año, **por separado en cada versión**. Eventos que comienzan antes o terminan después de 30 junio no se usan, aunque aparezcan en Q2 o Q3. Parsear la fecha completa real `YYYY-MM-DD HH:MM:SS.mmm`.
3. Emparejar por ID `id` literal exacto. Reportar la intersección, ID presentes solo en Q2 y solo en Q3. No inferir que dos IDs diferentes son el mismo acontecimiento, ni que desaparecieron víctimas.
4. Entre IDs coincidentes, contar cambios en `best`, `type_of_violence`, `country_id` y `date_start/end`; reportar suma de diferencias absolutas de `best`. Es una medición de revisión de registros, no de verdad final.
5. Para `type_of_violence = 1`, sumar `best` por ID admisible en cada edición y comparar totales globales y clasificación descriptiva de país con **≥25 muertes en enero–junio**, *solo dentro de la tabla de eventos Candidate observada*. Los países sin eventos no se declaran en paz; el umbral semestral NO es el objetivo anual GEO2027.
6. Incluir integridad: `q2_total_rows`, `q3_total_rows`, registros elegibles, resultados exactos por año, resumen combinado **sin presentar los años como independientes**. La salida debe generarse de los bytes oficiales y congelarse antes de interpretarla.
7. Es una auditoría de **revisiones de información registrada**. Las URLs históricas no acreditan fecha de publicación original; no etiquetar los orígenes como as-of cronológicamente certificados. No generar simulaciones de predicción con este contraste.

## Resultados verificados sobre seis archivos oficiales

La CI del repositorio ha descargado y procesado las **seis ediciones UCDP Candidate originales**, identificadas por URL, bytes y SHA-256; el informe [JSON congelado](../data/candidate-q2-q3-vintage-revisions.json) reproduce exactamente los valores calculados con el script [audit_candidate_q2_q3_vintages.py](../scripts/audit_candidate_q2_q3_vintages.py). Las fechas originales de publicación de los seis archivos NO están certificadas por este experimento. Los años 2024, 2025 y 2026 son cohortes correlacionadas y no replicaciones independientes de una habilidad de pronóstico.

| Enero–junio del año | Filas elegibles Q2 | Filas elegibles Q3 | IDs solo Q2 | IDs solo Q3 | IDs compartidos | IDs compartidos con cambio en `best` |
|---|---:|---:|---:|---:|---:|---:|
| 2024 | 12.922 | 14.380 | 442 | 1.900 | 12.480 | 208 |
| 2025 | 14.071 | 14.245 | 393 | 567 | 13.678 | 134 |
| 2026 | 10.038 | 10.723 | 207 | 892 | 9.831 | 89 |
| **Total descriptivo** | **37.031** | **39.348** | **1.042** | **3.359** | **35.989** | **431** |

**Importante:** «solo Q2» y «solo Q3» significan diferencias de IDs **dentro del mismo intervalo enero–junio**; un registro pudo cambiar de identificador o salir/entrar del corte por revisión de fechas. No son automáticamente eventos falsos ni eventos descubiertos por primera vez. El conjunto total Q3 de cada año también incluye julio–septiembre, pero esas filas se han filtrado y **no forman parte de la comparación**.

En los **35.989 emparejamientos por ID**: 431 filas cambian su mejor estimación de fallecidos; 147 cambian tipo de violencia, 234 cambian fecha y 1 cambia país. Son conteos de revisiones que pueden solaparse, no categorías mutuamente excluyentes. La suma absoluta de revisiones de `best` en filas compartidas alcanza **11.421**, dominada por 2025 (**7.736**); no significa que aumentaran o disminuyeran 11.421 víctimas reales.

### Sensibilidad del umbral semestral de 25 fallecimientos estatales

| Año | Fallecidos `best` estatales, Q2 | Mismo enero–junio reestimado en Q3 | Países con ≥25 en Q2 | Países con ≥25 en Q3 | Cruces hacia arriba / abajo |
|---|---:|---:|---:|---:|---|
| 2024 | 48.455 | 50.572 | 32 | 31 | 0 / 1 |
| 2025 | 64.923 | 60.126 | 31 | 32 | 1 / 0 |
| 2026 | 74.291 | 72.343 | 33 | 33 | 0 / 0 |

Estos totales son exclusivamente los `best` de los eventos Candidate que pasan el filtro de fechas y `type_of_violence=1`, **no estimaciones finales de víctimas ni la variable anual GEO2027**. Solo prueban que decisiones dependientes de umbrales pueden cambiar al revisar un mismo semestre.

### Identidad de los seis orígenes históricos

| Fuente | SHA-256 original |
|---|---|
| `24.01.24.06` | `dd1afaad1d0c06772daa762b623fcef036044528e654f29cb9b4143e1130d478` |
| `24.01.24.09` | `3f9f7acea9690cd8c5150981ae85b5a9365b2ca233f2b351b680de95cd4af390` |
| `25.01.25.06` | `8185c986f040ec2169728a7debf5fb1833426b534e846f51912046f78e4c6f7a` |
| `25.01.25.09` | `086362d535c61d1237f0824bee8afb6459bac71ca8d02026946b715264c910be` |
| `26.01.26.06` | `68dd3d363b8edf4808bd6bf6f5d0412c3c722ffb1db367aeb8eff48bab80589a` |
| `26.01.26.09` | `134da9b3df08b65266802c4b662e572f396c70c92ab62297319be657540bcede` |

**Conclusión específica:** la fuente Candidate tiene revisiones no triviales incluso en registros históricos de meses ya cerrados. Por eso sería engañoso construir un backtest de 30/90 días a partir de un único CSV acumulado retrospectivo sin controlar qué versión se conocía en cada origen. El siguiente paso debe estudiar **ediciones mensuales y su cronología de disponibilidad**, y elegir objetivos y baselines que toleren ese retraso; este estudio no demuestra por sí mismo *forecasting skill*.

## Secuencia y criterios para el desarrollo posterior

Después de fijar el informe, medir la tasa de revisión por tipo y país y cómo la definición de escalada depende de las versiones. Solo después reconstruir fechas de primera publicación, calendarios de orígenes y objetivos a 30/90 días, asociar referencias sencillas (persistencia, tasa histórica), y emitir predicciones futuras inmutables. No consultar ni sustituir cohortes congeladas GEO2027/28.

## Privacidad, publicación y trazabilidad

Trabajo institucional IDEA LAB sin referencias a perfiles, cuentas o repositorios personales. Solo publicar agregados de fuentes públicas y hashes, sin fichas de víctimas ni noticias reproducidas. Los informes exploratorios estarán diferenciados de cualquier futura puntuación prospectiva. Datos UCDP sujetos a atribución CC BY 4.0; fuente oficial: <https://ucdp.uu.se/downloads/>.
