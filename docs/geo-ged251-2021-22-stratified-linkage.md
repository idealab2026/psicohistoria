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
