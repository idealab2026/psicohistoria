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


## Resultados auténticos: ocho archivos originales y diez reconciliaciones exactas

El análisis ejecutado en GitHub Actions descargó y verificó los hashes
originales de **4 Candidate Q3 y 4 GED anuales** (GED22.1, GED23.1,
GED25.1, GED26.1), reprodujo los **10 casos** del estudio #154,
los estados de codificación `code_status`, los totales `best` y
la cantidad de IDs exactos que sobreviven dentro del mismo país/ventana.
El informe integra **solo agregados nacionales** y no publica IDs de
eventos. [Resultado JSON congelado](../data/candidate-ged-event-dyad-fates.json).

### Los cinco casos que no conservan el umbral T=5 en GED anual

| Año | País | Muertes `best` Candidate→GED | Eventos Candidate elegibles | IDs Candidate que siguen en GED (cualquier año) | Díadas Candidate presentes en GED estatal de ese año |
|---|---|---:|---:|---:|---:|
| 2024 | Brasil | 5→0 | 2 | 0/2 | 0/2 |
| 2024 | Bangladés | 5→0 | 2 | 0/2 | 0/2 |
| 2025 | Ecuador | 12→0 | 1 | 0/1 | 0/1 |
| 2025 | Brasil | 7→0 | 1 | 0/1 | 0/1 |
| 2025 | Libia | 7→0 | 2 | 0/2 | 0/2 |
| **Total de este subconjunto** | | **36→0** | **8** | **0/8** | **0/8** |

Los ocho registros Candidate carecen de **ID de evento exacto** en
los ZIP GED anuales de sus años, incluso buscando otros años del mismo
archivo. Sus identificadores `dyad_new_id` no están presentes entre
**ningún registro estatal del año del evento** en el GED anual
correspondiente. Es coherente con diferencias de criterios anuales
por díada, revisiones de codificación o fusiones; **ningún resultado
identifica causalmente cuál es el motivo**, y un cambio de ID
no demuestra que no ocurrieran hechos violentos. De hecho, Bangladés
figuraba `Clear` en Candidate.

### Descomposición de TODOS los diez países-año

La descomposición usa **IDs elegibles** y mantiene separadas las
muertes estimadas en Candidate de las estimadas en GED para un mismo
ID. Las sumas son exactas, comprobadas por código.

| Grupos | Eventos Candidate elegibles | Fallecidos Candidate `best` | Fallecidos GED `best` | ID compartidos elegibles | Muertes Candidate en IDs no compartidos | Muertes GED en IDs no compartidos |
|---|---:|---:|---:|---:|---:|---:|
| 2021–2022, 4 casos positivos conservados | 49 | 290 | 310 | 32 | 143 | 145 |
| 2024–2025, 6 casos, 1 conservado | 16 | 74 | 14 | 7 | 51 | 0 |
| **Total** | **65** | **364** | **324** | **39** | **194** | **145** |

La parte compartida de los cuatro casos tempranos cambia de
**147 a 165 muertes `best`** (diferencia +18). La parte
compartida reciente cambia de **23 a 14** (diferencia −9).
Los 51 fallecidos registrados en Candidate 2024–25
sobre IDs sin correspondencia elegible se descomponen en:
**36** procedentes de los cinco países que pierden toda la
etiqueta y **15** de Indonesia 2025, que sí conserva T=5.

La identidad comprobada para 2024–2025 es:
`14 GED − 74 Candidate = (14−23) − 51 + 0 = −60`.
Para 2021–2022:
`310−290 = (165−147) + 145 − 143 = +20`.
Estas son **reconciliaciones de estimaciones de fallecidos entre
ediciones**, no recuentos independientes de víctimas reales.

### Mecanismos observables adicionales

- **Togo, 2022:** el mismo ID elegible se mantiene, pero su
  estimación pasa de **8 a 23** (`+15 best`). Es un ejemplo
  verificable de **reestimación** que conserva el indicador.
- **Indonesia, 2025:** los 38 `best` Candidate pasan a 14 GED.
  Siete IDs compartidos pasan de **23 a 14** (`−9` por
  reestimación); un registro Candidate adicional con **15**
  `best` no conserva su ID (`−15`). No atribuir esos
  cambios directamente a desaparición de víctimas.
- **Turquía, 2021:** diez eventos conservan elegibilidad
  exacta y un ID registra **cambio de código de país**,
  sin impedir que el indicador del país siga positivo.
- **Israel, 2021:** veinte registros Candidate mantienen ID
  elegible; de los otros dieciséis, **15 IDs no aparecen
  en GED** y **uno figura recodificado a violencia no estatal
  o unilateral**. La díada de los dieciséis sigue representada
  entre los registros anuales estatales del mismo año.
  La etiqueta de Israel se mantiene gracias al total de los
  registros elegibles, no a la conservación perfecta de IDs.

En el conjunto de los diez casos, **39 de 65 eventos Candidate**
mantienen el mismo ID elegible para país/ventana. De los
**26 no compartidos**, **24 no aparecen en ninguna anualidad
del archivo GED**, uno cambia de país y otro cambia de tipo
de violencia. Los 17 no compartidos de 2021/22
(15 ausentes, uno de país cambiado y uno de tipo cambiado)
tienen **díada estatal presente en GED anual**; en
2024/25, ocho de los nueve no compartidos no la tienen.
El noveno es el caso de Indonesia y mantiene la díada.
Los códigos de díada son los de la base, no relaciones
de actores confirmadas externamente.

### Evaluación científica de la explicación

El patrón distingue **estabilidad de identificadores de díada**
frente a **estabilidad de identificadores de eventos**:
la desaparición de la etiqueta del país coincide con pérdida
del registro de la díada estatal con ID idéntico en la
primera GED anual, mientras que una etiqueta puede mantenerse
aunque muchos eventos se eliminen o recodifiquen por ID
si la díada continúa registrada. Esto apoya investigar
la selección anual de **díadas y conflictos** como
mecanismo relevante, coherente con la metodología oficial
de UCDP Candidate (criterios de inclusión más relajados).

**No demuestra que la misma díada real desapareciese**
(pudo cambiar su ID, codificación o alcance), ni que
el umbral de 25 muertes por díada-año sea la causa exacta
de esos ocho casos. Para atribuir causas se necesitan
tablas anuales de díadas, estado de actores, historial de
recodificación oficial y, cuando proceda, revisión manual
documentada. No inventar un emparejamiento entre
IDs no coincidentes.

Además, la muestra de **diez casos** fue seleccionada
retrospectivamente al conocer su resultado provisional.
No constituye evidencia prospectiva de capacidad de
anticipación. El producto Candidate y el producto
GED anual siguen siendo objetivos **distintos**.

**Próximo experimento defendible:** crear un análisis *dyad-year*
que coteje la presencia/ausencia de díadas Candidate en
la base oficial UCDP Dyadic anual, con ediciones y SHA
fijos, conservando claves de actor y tipo para evitar
emparejamientos espurios. Publicar negativos y aciertos
sin elegir umbrales a posteriori, y usar control
`as-of` estricto antes de emitir alertas nuevas.
