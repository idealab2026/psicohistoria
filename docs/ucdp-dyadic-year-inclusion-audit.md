# PSICOHISTORIA · UCDP Dyadic, comprobación externa de la elegibilidad anual (24-11-2026)

**Prerregistro de estudio descriptivo *posterior a seleccionar los diez casos*.** El estudio anterior #155 encontró que cinco etiquetas positivas de violencia estatal Candidate Q3 (mayo, ≥5 fallecidos, entre países Q1 con <5) desaparecían del primer GED anual, con ocho IDs de evento y ocho IDs de díada sin correspondencia idéntica. El propósito aquí es **verificar contra un dataset independiente oficial de díadas-año** si esas claves aparecen como *díada activa*; no buscar una nueva variable predictiva. Se prohíbe comparar con una edición GED posterior elegida por resultado.

## Fuentes y secuencia auditable

| Año de evento | Primer UCDP GED anual ya verificado | Primera edición **UCDP Dyadic** a examinar |
|---|---|---|
| 2021 | GED 22.1 | Dyadic 22.1 |
| 2022 | GED 23.1 | Dyadic 23.1 |
| 2024 | GED 25.1 | Dyadic 25.1 |
| 2025 | GED 26.1 | Dyadic 26.1 |

Los **cuatro CSV originales Candidate Q3** son los congelados en `data/candidate-ged-event-dyad-fates.json` y en los dos informes base, con URLs, longitudes y SHA. Los diez casos se extraen exactamente del informe #155 y deben reproducir país, año, total `best`, `code_status` y número de eventos elegibles. **Nunca cambiar esa muestra al observar Dyadic**.

Los **cuatro ZIP Dyadic oficiales** se recuperarán de los URLs de la Uppsala University de las ediciones citadas. Antes de leer sus datos, ejecutar el modo `--source-census` que registre solo **bytes, SHA-256, nombres de miembros ZIP y encabezados de columnas** (no filas ni resultados) en el log de CI. Fijar los cuatro SHA en código **antes** de la primera evaluación. Si alguno de los archivos no existe o el formato no es compatible, bloquear: no sustituir ediciones silenciosamente por la 26.1 o un espejo. Un modo `--check-report` debe reproducir exactamente el informe congelado.

## Unidad de observación y límites de inferencia

El conjunto UCDP Dyadic es **díada-año**, no evento ni país. La metodología UCDP exige, para codificarla como activa, al menos **25 muertes relacionadas con combates en un año natural por díada**. El periodo 1–30 mayo con umbral 5 fallecimientos `best` no equivale a ese criterio; las muertes GED y las de Dyadic pueden tener definiciones y revisiones diferentes.

En los 10 países-año:
1. Reconstruir las díadas `dyad_new_id` de eventos **Candidate Q3 estatales de fecha precisa y completamente contenidos en mayo 1–30**. No emparejar por nombre, geometría ni cercanía temporal. Los `dyad_new_id` faltantes se marcan sin clave, nunca se tratan como ausentes del conjunto oficial.
2. Verificar por país-año la suma `best`, `code_status` y nº de eventos contra el informe #155; casos de ID de evento duplicado, `best` negativo, fechas ilegales o SHA distinta bloquean. Una díada puede tener **múltiples eventos**: contar `n` de díadas **únicas** y sus muertes, además del `n` de eventos, evitando multiplicar pruebas por evento.
3. Para cada díada con clave original, comprobar **exactamente** la pareja `(dyad_id, year)` en la edición histórica correspondiente; no aceptar solo `dyad_id` en otro año como activo en el año evaluado. Registrar también `same_dyad_id_any_year` como contraste de historial, sin inferir actividad anual.
4. Contrastar los resultados por grupos **etiqueta anual GED retenida/no retenida** y por año; para los cinco países perdidos, distinguir `none of candidate dyads active in official dyadic-year` vs `one or more active`. Esto es diagnóstico de inclusión, no prueba de que los registros Candidate fueran inventados.
5. Comparación auxiliar **cobertura parcial Candidate enero–septiembre** por las mismas díadas, con eventos estatales tipo1, fecha precisa totalmente dentro de ese periodo. Es un *límite temporal inferior incompleto* de fallecidos `best` Candidate, no el conteo anual Dyadic, no el mismo concepto ni un chequeo de exactitud contra 25. No extrapolar octubre–diciembre.
6. Si el CSV oficial dispone de `side_a_id`, `side_b_id`, `conflict_id` y `version`, conservar solo estadísticas de disponibilidad y comparabilidad, sin crear matching especulativo a partir de nombres. No publicar claves de identificación de eventos o díadas ni listados detallados de actores; solo tablas agregadas nacionales.

**Control contextual:** el informe #155 observa 8/8 eventos de cinco casos perdidos sin `dyad_new_id` coincidente en el GED anual estatal del mismo año y 17/17 eventos no compartidos de 2021/22 cuya díada sí aparece. Hay que **contrastar** esto con las nuevas tablas oficiales Dyadic, no asumir que coincidirán.

## Interpretación predefinida

- Si una díada Candidate está **ausente del Dyadic de ese año**, el código *no la registra activa como díada-año bajo las reglas de esa edición*. Esto respalda una explicación de **inclusión/recodificación**, pero NO demuestra específicamente que su recuento anual real fuera <25 ni que la violencia no ocurriera.
- Si hay díadas Candidate **presentes en Dyadic** pero no aparecen sus IDs en GED anual del mismo año, registrar **inconsistencia de correspondencia o diferencias entre productos**. No imponer la hipótesis de exclusión con un falso positivo.
- No inferir que una pérdida de identidad del `dyad_id` implique desaparición del par de actores: UCDP puede reasignar identificadores cuando hay escisión/coalición o cambian identidades de grupo.
- **Importante:** toda comparación con Dyadic anual es *hindsight* y NO se puede usar como feature para una alerta emitida antes de cerrar el año.
- No tocar las cuatro cohortes de probabilidades prospectivas de GEO2027/GEO2028/NEWCONF2027/ACD2027 (620 pronósticos); no declarar aciertos de 2026. Privacidad institucional intacta.

Fuentes: [portal UCDP](https://ucdp.uu.se/downloads/), [ediciones históricas](https://ucdp.uu.se/downloads/olddw.html), [UCDP Dyadic codebook 25.1](https://ucdp.uu.se/downloads/dyadic/ucdp-dyadic-251.pdf), cuya unidad de observación y regla anual de 25 muertes constituyen la definición del estimando dyad-year.


## Registro de fuentes originales: censo sin resultados y análisis posterior

La [CI de censo de fuentes](https://github.com/idealab2026/psicohistoria/actions/runs/45413445161)
ha recuperado los cuatro ZIP originales y **únicamente ha examinado
bytes, SHA, nombres de archivo CSV y encabezados**. Los cuatro
archivos contienen `dyad_id`, `year`, `conflict_id`, `side_a_id`
y `side_b_id`. Solo posteriormente se fijaron estos SHA en el
programa para evaluar los registros:

| Año de evento | UCDP Dyadic, edición de primera publicación anual | SHA-256 ZIP oficial | Registros díada-año para el año estudiado |
|---|---|---|---:|
| 2021 | 22.1 | `4b20a049560db91bba52b1c4062ffbfedd706da8eed71928cbbba444da9ea538` | 64 |
| 2022 | 23.1 | `748daa222c45d2e4b43930640ff79ff8b585c3ac404f5dc192776876ef8dd9d1` | 64 |
| 2024 | 25.1 | `e34d26c39d23739ab65bc52fd42747aa88e7ecdf84d16c7bacafd590ed767330` | 68 |
| 2025 | 26.1 | `1f89ca62c82819ecfcd8dd483826bc6760530118ddc63a191a9d4252a2174557` | 78 |

Los otros cuatro originales son las ediciones UCDP Candidate Q3
ya protegidas por SHA desde #155. En total el estudio reproduce **ocho
fuentes originales**, pero no republica las fichas individuales.

[Informe agregado con controles de originales](../data/ucdp-official-dyadyear-case-resolution.json).

## Evidencia: actividad de una díada durante el año no equivale a elegibilidad histórica

En los 10 países-año Candidate positivos T≥5 de mayo:

| Año | País | Mantiene T≥5 en GED anual | Díadas Candidate distintas | Activas en Dyadic ese año | Activas alguna vez en esa edición |
|---|---|---|---:|---:|---:|
| 2021 | Perú | Sí | 1 | 0 | 1 |
| 2021 | Turquía | Sí | 1 | 1 | 1 |
| 2021 | Israel | Sí | 2 | 2 | 2 |
| 2022 | Togo | Sí | 1 | 1 | 1 |
| 2024 | Brasil | No | 2 | 0 | 0 |
| 2024 | Bangladés | No | 1 | 0 | 0 |
| 2025 | Ecuador | No | 1 | 0 | 0 |
| 2025 | Brasil | No | 1 | 0 | 0 |
| 2025 | Libia | No | 1 | 0 | 0 |
| 2025 | Indonesia | Sí | 1 | 1 | 1 |

**Contraste nacional, solo estos diez ejemplos postseleccionados:**
los cinco países que dejan de superar T=5 en GED anual
tienen **0/6 díadas Candidate con misma clave activas en
cualquier año de la primera edición Dyadic**.
Los cinco países que sí mantienen el indicador tienen
**6/6 díadas Candidate con clave activa en algún año** de esa
edición. Al exigir el **mismo año**, solo 5 de esas 6
díadas figuran activas y **Perú constituye la excepción**.

**Perú, 2021**: GED22.1 conserva 16 fallecimientos estatales
bajo las reglas del estudio, pero la misma clave de díada
no aparece activa en Dyadic22.1 para **2021**; sí está
presente en **otro año anterior** dentro de esa edición.
No es una contradicción de UCDP. Según su
[metodología oficial](https://www.uu.se/en/department/peace-and-conflict-research/research/ucdp/ucdp-methodology.html),
GED conserva los eventos de díadas que **hayan superado las
25 muertes en algún año**, incluso si en un año particular no
cumplen ese umbral. Dyadic registra únicamente sus **años activos**.
El [manual oficial de UCDP Candidate](https://ucdp.uu.se/downloads/candidateged/ucdp-candidate-codebook%201.1.pdf)
explica además que Candidate contiene provisionalmente
eventos de díadas que aún no cumplen los criterios de
inclusión anual.

Por tanto, la variable retrospectiva que describe la
correspondencia entre las fuentes no es solo
`active(year)`, sino **`ever_active(as_of_annual_version)`**,
registrada exactamente con el ID de díada original.
No sabemos que ese estado pudiera conocerse sin
fuga temporal en la fecha de una supuesta alerta Candidate;
solo lo conocemos tras cerrar GED y Dyadic anuales.

## Muertes Candidate y edición anual: separadas por fuente

En las diez observaciones positivas originales se contabilizaron
**364 muertes `best` en Candidate mayo**, sin corregir.
El reparto por la **actividad durante el año** de sus díadas fue:

| Clasificación Dyadic (mismo año) | Fallecidos Candidate de mayo |
|---|---:|
| En díadas que Dyadic marca activas ese año | 312 |
| En díadas no activas ese año | 52 |
| **Total** | **364** |

De las 52 muertes en díadas inactivas ese año, **16**
corresponden a Perú (díada activa en otro año), y
**36** a los cinco países que pierden la etiqueta GED anual
(díadas que no figuran activas en ninguna anualidad de
la edición histórica consultada). Estos recuentos
Candidate no son *battle-related deaths* anuales Dyadic
ni corresponden exactamente a su umbral de 25.

## Conclusión y límites

El cotejo con una **segunda familia oficial de UCDP**
respalda fuertemente —en estos diez casos seleccionados—
una explicación de la pérdida de etiquetas basada en
**elegibilidad histórica de las díadas**. El manual de
UCDP confirma que los eventos GED pueden persistir en
años subumbrales de díadas previamente activas,
mientras Candidate admite registros todavía pendientes
de inclusión.

Pero esto **no demuestra** que ninguna de las seis
díadas de los cinco casos perdidos fuese real o ficticia:
una clave ausente puede haber sido recodificada, fusionada,
dividida o clasificada bajo actores/tipos distintos.
No se han reconstruido identidades de actores a mano ni
hecho *fuzzy joins*. La separación perfecta 5/5 frente
a 0/5 es **postselección**, no pronóstico ni prueba de
generalización fuera de los diez casos.

**Decisión científica:** cualquier futura tarea de
*forecasting* debe distinguir entre (a) probabilidad
de violencia medida con Candidate y (b) probabilidad
de satisfacer los criterios anuales de las díadas GED.
Los indicadores de actividad/elegibilidad tomados de
la edición GED/Dyadic posterior son **fuga temporal**
y nunca deben usarse como insumos de previsiones
emitidas antes del cierre. Las 620 probabilidades
prospectivas anteriores permanecen intactas y
no se han certificado nuevas alertas de 2026.
