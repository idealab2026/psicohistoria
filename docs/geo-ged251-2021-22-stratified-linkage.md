# PSICOHISTORIA · Auditoría GED25.1 internacional: ambigüedad espacio-temporal

**Protocolo preregistrado en Git el 19/11/2026, antes de extraer la nueva muestra.** Continuación de la [PR #134](https://github.com/idealab2026/psicohistoria/pull/134) y de la auditoría específica de Burundi.

## Problema y estimando

La base oficial [UCDP GED 25.1](https://ucdp.uu.se/downloads/olddw.html) registra episodios de violencia letal con **precisión geográfica variable**. La [documentación técnica de GED25.1](https://ucdp.uu.se/downloads/ged/ged251.pdf) incluye `where_prec`, fecha inicial/final y `type_of_violence`. Un centroide administrativo repetido puede coincidir en coordenadas aun cuando los episodios, víctimas o fuentes sean diferentes.

**Estimando de esta fase:** frecuencia descriptiva en una muestra determinista estratificada de *candidatos a revisión por proximidad espacio-temporal*, no duplicaciones comprobadas, no errores de UCDP, no validación de fallecimientos. El denominador son **24 anclas seleccionadas**, no todos los eventos GED.

## Muestreo predefinido

1. **Universo:** archivo GED25.1 oficial fijado por SHA-256 `e256f1fb20a579d8b2f910e5bae212f486d3002adaa2e4359ace740c737da05d`. Filtrar años **2021 y 2022**, los **196 GWNO** originales de GEO2027 (solo identificadores, sin probabilidades), `type_of_violence=1`, `best>=1`, fechas inicial y final dentro del año GED, lat/lon válidos y `where_prec` en 1–7. No imputar valores faltantes como cero.
2. **Cuatro estratos (6 anclas cada uno):** fecha puntual y precisión espacial alta (`where_prec=1–2`), fecha puntual y baja (`3–7`), intervalo de fechas y alta, intervalo y baja. `where_prec=2` indica proximidad aproximada, **no** exactitud de coordenadas.
3. **Selección estable independiente de coincidencias:** ordenar dentro de estrato por SHA256 de `IDEALAB-20261119-GED251-2021-22-FOUR-STRATA-V1|<GED id>`; priorizar una ancla por país dentro de cada estrato, rellenar sin esa preferencia si no hay seis países disponibles. Este muestreo **no es proporcional al universo**. El diseño, estratos, fecha y semilla se fijan en este commit antes de ejecutar el estudio.
4. **Vecindad:** entre otros eventos **de la misma edición, mismo GWNO y año**, calcular distancia haversine entre coordenadas y distancia mínima entre intervalos de fechas. Comparar controles de solo lugar ≤25 km, solo tiempo ≤3 días, ambos ≤25 km y ≤3 días, ambos ≤100 km y ≤3 días, y criterio más estricto ≤5 km y solapamiento de intervalos (gap 0 días). Separar vecinos donde ambos eventos tengan `where_prec<=2`.
5. **Resultado:** número de anclas con alguna coincidencia en cada criterio, estratos, IDs y metadatos mínimos de anclas/vecinos (sin republicar textos de fuentes ni personas). **Un vecino no está etiquetado como duplicado**. Cero revisiones manuales hasta que se realice contraste documental externo.

Los eventos de tipos 2 y 3 quedan fuera porque el objetivo GEO es `sb_total_deaths_best>=25`, de violencia estatal. Evitar confundir *intervalos temporales* con fecha de fallecimiento confirmada; no usar coordenadas GED como precisión puntual forense.

## Evaluación y decisiones

Se ejecuta con fuentes originales del servidor UCDP y verifica el SHA del ZIP antes de calcular cualquier métrica. No se descarga ACLED ni GDELT ni se atribuye independencia documental por coincidencia entre registros **de la misma UCDP**. La publicación solo se aceptará tras comparar el resultado calculado con el JSON congelado y pasar las pruebas adversariales + auditoría de privacidad.

La siguiente fase añadirá **revisión ciega, documentada y humana** de pares candidatos y controles sin coincidencia; entonces, y solo entonces, será razonable discutir una estimación de falsos emparejamientos con intervalos de incertidumbre. Aunque un caso local se corrija, no implica que cambie el estado country-year `>=25`; para recalcular Brier hace falta recomputar con etiquetas y cohortes compatibles, manteniendo inmutables las predicciones emitidas.

**Reproducibilidad:**

```sh
python3 -B -m unittest discover -s scripts -p 'test_audit_geo_ged251_stratified_linkage.py' -v
python3 -B scripts/audit_geo_ged251_stratified_linkage.py --check-report
python3 -B scripts/audit_public.py
```

**Fuentes y límites:** [descarga histórica UCDP](https://ucdp.uu.se/downloads/olddw.html), [codebook GED25.1](https://ucdp.uu.se/downloads/ged/ged251.pdf). El archivo oficial SHA fija sus bytes accesibles en la ejecución, no una prueba notarial de publicación en 2025. La muestra de anclas resulta reproducible, pero no es una muestra simple representativa de países o episodios y no autoriza extrapolar una tasa global de duplicación.

## Primer resultado oficial reproducido: cohorte GED25.1

La ejecución oficial UCDP GED25.1, con ZIP de **385.918 registros** y SHA-256 correcto, dejó **20.716 eventos elegibles** de violencia estatal en los años 2021–2022 y los 196 GWNO de la cohorte. El muestreo SHA estratificado seleccionó exactamente **24 anclas de 14 países distintos**.

| Estrato predeterminado | Elegibles del universo | Anclas seleccionadas | Con vecino ≤25 km y gap ≤3 días |
|---|---:|---:|---:|
| Fecha puntual + precisión espacial 1–2 | 11.528 | 6 | 4 |
| Fecha puntual + precisión espacial 3–7 | 4.562 | 6 | 3 |
| Fecha intervalo + precisión espacial 1–2 | 2.092 | 6 | 5 |
| Fecha intervalo + precisión espacial 3–7 | 2.534 | 6 | 2 |
| **Total** | **20.716** | **24** | **14** |

**Comparación de filtros sobre las mismas 24 anclas:** 21 tienen alguna fila del mismo país-año a ≤25 km sin restringir la fecha; 16 tienen algún vecino a ≤100 km y gap ≤3 días; 14 a ≤25 km y gap ≤3 días; 5 a ≤5 km y con intervalos solapados. De las 24, **8** tienen al menos un vecino a ≤25 km, gap ≤3 días y precisión espacial `where_prec<=2` en **ambos** registros.

La combinación de filtro espacial y temporal reduce coincidencias sospechosas, **pero no ofrece ninguna verificación de identidad**. Algunos vecinos están a distancia 0 por uso de centroides o coordenadas compartidas y pueden ser episodios distintos. El muestreo no fue diseñado para estimar tasas del universo: cuatro estratos reciben idéntica cuota aunque sus poblaciones sean muy diferentes. No presentar 14/24 como porcentaje de errores de GED, duplicaciones o aciertos de GEO.

**Estado de la verdad documental:** 0 pares revisados manualmente, 0 duplicados comprobados, 0 verificaciones independientes de víctimas obtenidas y **ninguna etiqueta o probabilidad GEO reemitida**. Estos ceros designan el trabajo de adjudicación realizado, no una demostración de ausencia de problemas.

Evidencia reproducible: [JSON de la muestra y sus 24 anclas](../data/geo-ged251-2021-22-linkage-sample24.json), [implementación](../scripts/audit_geo_ged251_stratified_linkage.py). El CI ejecuta ahora `--check-report` para rechazar cualquier revisión silenciosa del resultado.
