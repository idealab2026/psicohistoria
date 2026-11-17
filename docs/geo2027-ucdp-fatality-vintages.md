# GEO2027 — Incertidumbre de recuento y revisiones históricas UCDP

**Protocolo de auditoría retrospectiva (17 de noviembre de 2026).** El objetivo original para 2027 permanece `sb_total_deaths_best >=25`; las 196 probabilidades de GEO2027, sus sombras y las 15 alertas siguen congeladas. No hay resultados observables de 2027 y **ningún Brier futuro se calcula aquí**.

## Pregunta falsable

¿Con qué frecuencia la clasificación binaria >=25 cambia cuando UCDP informa `sb_total_deaths_low`, `sb_total_deaths_best`, `sb_total_deaths_high` en el **mismo archivo**, y en qué medida **las revisiones entre archivos** alteran esas clasificaciones para los mismos países-año?

Son incertidumbres distintas. Las discrepancias entre las tres estimaciones son **sensibilidad a la medición codificada de fallecidos**, no intervalos de confianza ni una distribución. El propio UCDP puede registrar `best > high` y, por ello, no se supone un orden fijo. Una modificación entre 23.1 y 26.1 es **revisión retrospectiva de los datos**, no otra realización de un experimento independiente.

## Diseño congelado

* Fuente: cuatro ficheros oficiales UCDP OrganizedViolenceCY 23.1 (XLSX), 24.1, 25.1 y 26.1 (CSV comprimido). Se comprueba el **SHA-256 exacto** de los archivos ya utilizados por PSICOHISTORIA, el total de filas país–año y su unión con `sb_total_deaths_best` de los análisis anteriores.
* Universo: los **196 GWNO** del primer pronóstico GEO2027. La cobertura anual completa existe desde **2011**; hay 54 observaciones *año×edición* de 196 países desde 2011 hasta los cortes de cada edición (2022, 2023, 2024, 2025). Son bloques correlacionados y retrospectivamente revisados.
* Auditoría visible reciente: **10 combinaciones año×edición** para 2022–2025; se desglosan los tres recuentos de países que superan 25, las discrepancias binarias entre cada pareja de estimadores, la cantidad cuyo umbral cruza `min(low,best,high)<25<=max(low,best,high)`, las inversiones de orden en la fuente y los identificadores GWNO implicados.
* Revisiones: **10 comparaciones de pares de ediciones para un mismo año** en 2022–2024. Se separa el número de países que cambia en la etiqueta `low`, `best`, `high` y en la pertenencia al conjunto de países cuyo umbral resulta ambiguo.
* Reglas negativas: jamás se imputan ceros a países ausentes; se rechazan duplicidades, negativos y decimales; los casos `low>best` o `best>high` se **conservan y auditan** (no se corrigen ni descartan). No se usa 2026 ni 2027, no se reentrenan modelos, y ninguna clasificación incierta se utiliza para declarar un ganador histórico.

## Lectura científica

`min(low,best,high)<25<=max(low,best,high)` es una condición **de sensibilidad del resultado a la estimación**, no la probabilidad de que un conflicto haya ocurrido. Un país puede seguir codificado como 0 si UCDP no incluye ciertos eventos conforme a sus criterios. No se deben promediar los 54 bloques como si fueran muestras independientes, ni multiplicar por 196 para inventar tamaño muestral efectivo. En las ediciones sucesivas se observan en gran medida **los mismos 196 países**.

La capacidad de calcular la sensibilidad prospectiva 2027 —si alguna vez existe la primera edición completa de 2027, desde 2028— permanece en `scripts/audit_geo2027_fatality_intervals.py`, incorporada por PR #105. El presente estudio **no cambia esa regla primaria** ni realiza scoring sobre las predicciones congeladas.

Los resultados exactos, solo después de reconstrucción y comprobación contra los archivos oficiales, se guardarán en `data/geo2027-ucdp-fatality-vintage-intervals.json`. Las pruebas sintéticas no constituyen resultados empíricos. El script oficial es `scripts/audit_geo2027_ucdp_fatality_vintages.py`.

**Control adicional:** la anterior versión del futuro validador (PR #105) suponía que `low<=best<=high`; esta revisión elimina esa suposición y añade pruebas sintéticas adversariales con `best>high`. La etiqueta prospectiva primaria con `best` es intocable.

## Fuentes

UCDP, [Dataset Download Center](https://ucdp.uu.se/downloads/) y [Historical Versions](https://ucdp.uu.se/downloads/olddw.html). UCDP OrganizedViolenceCY Codebooks de las cuatro ediciones. Los derechos y condiciones de cita de UCDP se mantienen; no se redistribuyen archivos de origen en este repositorio.

**Privacidad:** investigación publicada únicamente bajo IDEA LAB, sin enlaces a identidades o repositorios privados.
