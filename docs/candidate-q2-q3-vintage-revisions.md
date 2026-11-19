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

## Secuencia y criterios para el desarrollo posterior

Después de fijar el informe, medir la tasa de revisión por tipo y país y cómo la definición de escalada depende de las versiones. Solo después reconstruir fechas de primera publicación, calendarios de orígenes y objetivos a 30/90 días, asociar referencias sencillas (persistencia, tasa histórica), y emitir predicciones futuras inmutables. No consultar ni sustituir cohortes congeladas GEO2027/28.

## Privacidad, publicación y trazabilidad

Trabajo institucional IDEA LAB sin referencias a perfiles, cuentas o repositorios personales. Solo publicar agregados de fuentes públicas y hashes, sin fichas de víctimas ni noticias reproducidas. Los informes exploratorios estarán diferenciados de cualquier futura puntuación prospectiva. Datos UCDP sujetos a atribución CC BY 4.0; fuente oficial: <https://ucdp.uu.se/downloads/>.
