# PSICOHISTORIA — Destino de los eventos Candidate al pasar a GED anual (24-11-2026)

**Diseño de diagnóstico, post-selección y no causal, fijado ANTES de examinar los registros individuales de GED para este nuevo análisis.** Continuación de la comparación de 10 países-año Candidate positivos T=5/mayo y primera versión GED anual publicada en los estudios PR #151, #152 y #154. No generar probabilidades; no pretender validar capacidad de alerta prospectiva.

## Fuentes y bloqueo

Descargar **exactamente 4 Candidate Q3 acumuladas** (septiembre 2021, 2022, 2024, 2025) y **4 archivos GED anuales** correspondientes a esos mismos años de evento en sus primeras ediciones: GED22.1, GED23.1, GED25.1 y GED26.1. Verificar **URL, tamaño (si consta), SHA-256 original** contra los informes institucionales ya congelados `data/candidate-ged-2021-22-resolution.json` y `data/candidate-to-annual-ged-resolution.json`. No permitir descargas alternativas, último GED para años antiguos ni parámetros seleccionados mirando resultados.

La fuente de casos es `data/candidate-ged-retention-strata.json`: exactamente **10 pares (año, país)** con Q1 Candidate estatal best<5, Q3 Candidate estatal best≥5 entre 1–30 mayo; informes previos exigen **642 país-años en riesgo** y cinco positivos conservados en GED. Verificar SHA de los dos informes públicos del origen tal como constan en el propio informe estratificado. Verificar el mismo universo canónico de 196 países/año.

## Definiciones y reconciliación exacta de fallecidos

Solo se admite, para estimar T=5/mayo: `type_of_violence=1`, `date_prec in {1,2}`, `country_id` del caso, evento **íntegramente** dentro de 1–30 mayo y `best≥0`. GED anual se filtra por **año del acontecimiento**, no año de edición.

Para cada uno de los diez casos:
1. Extraer todos los **eventos Candidate Q3 elegibles**, clasificando `code_status`, muertes `best` y su ID; comprobar que **el total best**, el número de eventos y el desglose de status coinciden exactamente con el informe congelado.
2. Extraer los **eventos GED anuales elegibles del mismo país/ventana**; comprobar su total `best` contra el informe congelado.
3. Hacer unión por **ID exacto de evento** —identificador de registro, **no** identidad incontrovertible del acontecimiento—. Separar:
   - `shared_eligible_same_id`: ID elegible en ambas bases, mismo país, violencia estatal y ventana, con las muertes Candidate y GED por separado.
   - `candidate_only_eligible`: IDs elegibles Candidate que no son elegibles GED de ese país/ventana. Clasificación exclusiva en `id_absent_from_annual_all_years`, `id_found_in_different_event_year`, `id_reassigned_country`, `id_retyped_nonstate_or_unilateral`, `id_changed_temporal_precision`, `id_moved_outside_window`. Usar ese orden **solo para conteo exclusivo**; además contar flags simultáneos por separado.
   - `annual_only_eligible`: IDs elegibles GED para país/ventana que **no aparecen entre los elegibles Candidate**; no afirmar que sean acontecimientos nuevos.
4. Reconciliar exactamente:
   `candidate_best = shared_candidate_best + candidate_only_best`;
   `annual_best = shared_annual_best + annual_only_best`;
   `annual_best - candidate_best = (shared_annual_best-shared_candidate_best) + annual_only_best - candidate_only_best`.
   Bloquear si no se cumple cualquiera de las tres identidades.
5. Comparar `dyad_new_id` en IDs compartidos cuando ambas fuentes lo admitan; registrar `dyad_id_changed` sin equipararlo a cambios reales de actor. Para **eventos Candidate cuyos ID no entran en GED**, comprobar si el mismo `dyad_new_id` está presente en **algún evento GED estatal del mismo año**. No confundir ausencia de díada con ausencia de violencia: la díada puede haber sido recodificada, filtrada o fusionada.
6. Publicar por país-año **solo agregados** de eventos, muertes, code status, dyad-ID compartido/cambiado/ausente y causas observables de no coincidencia. **No** publicar IDs ni descripciones de registros individuales. Comparar descriptivamente entre 2021–22 y 2024–25, sin estimar un nuevo modelo de falsos positivos.

## Controles antivicio

- Hash de archivos fuente, esquema mínimo y columna `dyad_new_id` declarada si existe. Si falta, declarar no disponible, no inventar identificadores. Considerar que un ID de díada solo es interpretable junto al tipo de violencia; cotejar díadas de tipo1 en el mismo año.
- IDs de evento vacíos/repetidos, `best` negativo, país, tipo, precisión o fechas ilegales: bloquear. Ventanas fijas, no prorratear intervalos.
- Antes de mostrar resultados, exigir que el mismo caso del informe #154 conserve su `best` y `code_status`. Si no, bloquear incluso si los agregados suman lo mismo pero se redistribuyen por status.
- Reproducibilidad: ejecución de GitHub Actions con fuentes originales remotas SHA-pinned, pruebas sintéticas adversariales de cambios de fecha/tipo/país/díada, ausencia de ID y ecuaciones de reconciliación; segunda ejecución valida objeto JSON exacto contra informe congelado.
- No «emparejar» eventos por proximidad geográfica, fecha o nombre de actor: eso introduciría correspondencias especulativas. Los IDs no emparejados se etiquetan **no vinculados por ID**, jamás «eventos falsos».
- **Fuente de sesgo:** los 10 casos se eligieron porque ya dieron resultados Candidate positivos; GED anual es posterior y no utilizable como característica predictiva antes del acontecimiento. Ningún valor p ni ranking de calidad.
- Preservar los pronósticos congelados GEO2027, NEWCONF2027, ACD2027 y GEO2028, los datos privados y la lista institucional de publicaciones. Prohibido crear vínculos con identidades/repositorios personales.

## Interpretación predefinida

Si la pérdida de etiquetas se concentra en IDs Candidate ausentes del GED anual, eso **apoya un mecanismo de exclusión o recodificación de registros**, no demuestra que los eventos no ocurrieran. Si los mismos IDs permanecen elegibles pero sus `best` cambian, cuantificar un componente de **reestimación de fallecidos**. Si hay IDs que cambian tipo, país, año o ventana, mostrarlos separadamente. La ausencia de `dyad_new_id` en GED puede ser compatible con la aplicación anual de reglas por díada, pero no confirma causalmente ese proceso.

Referencia conceptual: [Hegre et al. 2020, UCDP Candidate](https://doi.org/10.1177/2053168020935257), que documenta diferencias y criterios de inclusión Candidate/GED. No se emitirán alertas de corto plazo con estas retrospectivas ni se tratará 2026 como resuelto por GED anual.
