# GEO2027 — Auditoría de ceros codificados y universo oficial de 196 países

**Fuente primaria:** [UCDP Country-Year Dataset on Organized Violence within Country Borders, Codebook 26.1](https://ucdp.uu.se/downloads/organizedviolencecy/UCDP_OrganizedViolenceCY_Codebook_261.pdf), páginas 2–4. Fecha de auditoría: **16 de noviembre de 2026**. **Cero resultados oficiales de 2027 resueltos**.

## Pregunta y corrección epistemológica

El objetivo congelado de GEO2027 es pronosticar si el país supera **25 muertes estatales codificadas como `sb_total_deaths_best`** en el agregado país–año de UCDP OrganizedViolenceCY, edición 2027 futura. No equivale a predecir toda la violencia política, todos los conflictos, todas las víctimas ni ausencia de riesgo real.

El manual oficial UCDP 26.1 deja explícito que:

1. El conjunto está construido a partir de UCDP GED y abarca los **estados Gleditsch–Ward existentes en cada año**, incluidos los países–año que carecen de eventos incluidos.
2. El **0 de fallecidos es un valor codificado**, que puede coincidir con violencia real que **no cumple los criterios de inclusión** de GED y sus díadas/actores. La recopilación de hechos de una díada/actor depende de que haya superado el umbral de inclusión (25 muertes en un año); en años anteriores a ese primer cruce se excluyen hechos por debajo del umbral. Por tanto, `sb_total_deaths_best == 0` **no autoriza** afirmar «sin violencia», «sin víctimas» ni «no hay guerra».
3. El campo booleano `sb_exist`/`sb_exist_cy` indica la **existencia de sucesos estatales recogidos**, no la «activación» del conflicto bajo el umbral estadístico del proyecto. Un dato con `sb_exist = 1` y 0 muertes codificadas constituye una señal especialmente clara de que las medidas no son intercambiables. La prueba *no presupone* que tales filas existan en todos los años o ediciones: las cuenta.
4. **Un 0 existente en una fila oficial** es distinto de **una fila país–año inexistente**. Solo el primer caso permite producir una etiqueta 0 cuando el objetivo futuro es «25+ muertes codificadas».

Esto no cambia los coeficientes ni la función objetivo de las tres emisiones de 2027. **Corrige su interpretación y protege la resolución futura de etiquetas.**

## Diseño de auditoría reproducible

El script `scripts/audit_geo2027_ucdp_zero_coding.py` descarga y verifica los SHA archivados de las **cuatro ediciones oficiales** UCDP 23.1, 24.1, 25.1 y 26.1. Exige los mismos conteos, total de filas, años y universo que los análisis originales del laboratorio:

| Versión UCDP | Año final | Archivo fuente | Registros país–año esperados |
|---|---:|---|---:|
| 23.1 | 2022 | XLSX | 6.544 |
| 24.1 | 2023 | CSV-ZIP | 6.740 |
| 25.1 | 2024 | CSV-ZIP | 6.936 |
| 26.1 | 2025 | CSV-ZIP | 7.132 |

Además de `sb_total_deaths_best`, extrae el campo `sb_exist` con un lector propio de XLSX heredado (sin macros ni ejecución) y otro de los CSV oficiales. **Cada una de las anotaciones se cruza por GWNO y año con el recuento previamente SHA-verificado**. Si una cifra, columna, fila o identificador no coincide, la publicación falla.

Se publica por cada origen 2022–2025 y edición disponible el número de filas **explícitas** de los 196 países que fueron congelados para 2027; el desglose de recuentos exactamente 0, de 1–24 y de ≥25, la existencia estatal `sb_exist`, los ceros con bandera de existencia 1 y los recuentos positivos con bandera 0. Se calcula la cobertura anual desde 1989 (algunos estados no existían aún, por lo que **no deben imputarse países antiguos que no estuvieran presentes**). Entre versiones históricas se documenta cuántos países cambian el indicador de «cero fatalidades codificadas» o su bandera de existencia, sin interpretar revisiones retrospectivas como resultados prospectivos.

## Resultados reconstruidos y auditados contra los originales oficiales

**Todas las cuatro ediciones superaron la comprobación SHA, la igualdad de recuentos país–año y la verificación de la bandera `sb_exist`.** En las cuatro, desde el año **2011** están presentes los **196 GWNO del primer pronóstico de 2027** sin ninguna fila ausente. Antes de 2011 algunas entidades del conjunto actual no existían o no estaban registradas como estados en los años anteriores: **no deben fabricarse filas históricas para completar 196**.

| Edición | Año objetivo observado | Filas explícitas sobre los 196 | Muertes codificadas = 0 | Muertes 1–24 | Muertes ≥25 | Ceros con `sb_exist=1` |
|---|---:|---:|---:|---:|---:|---:|
| 23.1 | 2022 | 196 | 145 | 14 | 37 | 0 |
| 24.1 | 2023 | 196 | 150 | 12 | 34 | **1** |
| 25.1 | 2024 | 196 | 153 | 8 | 35 | 0 |
| **26.1** | **2025** | **196** | **154** | **8** | **34** | **0** |

El caso **2023** demuestra que puede coexistir un **cero oficial de `sb_total_deaths_best` con bandera `sb_exist=1`**. Ese caso existe en las ediciones 24.1, 25.1 y 26.1 y no cambia el objetivo del proyecto: para la variable binaria **≥25 fallecidos codificados** su etiqueta es 0, no 1.

En el origen 2022, las ediciones 23.1 y 24.1 no registran ningún cero con bandera de existencia 1; **25.1 y 26.1 sí registran uno**. En 2025 no aparece esa combinación. **Eso no significa que en todos los países con cero muertes no hubiera violencia**, porque el manual documenta también exclusiones por el umbral de inclusión de díadas/actores.

### Revisión de fuentes y construcción del panel

- 2022: UCDP 23.1 registra **145 ceros**, mientras 26.1 registra **144**; entre ellas cambia **un país de la condición «cero codificado»** y **dos países de la bandera de existencia estatal**. Para la comparación 24.1→26.1, la bandera de existencia cambia en un país aunque el indicador de cero no.
- 2023: el indicador de cero y la bandera de existencia coinciden exactamente entre las ediciones 24.1, 25.1 y 26.1 para los 196 países.
- 2024: ambos indicadores coinciden entre 25.1 y 26.1 para los 196 países.
- No hay edición anterior a 26.1 que observe oficialmente el **año 2025**; no pueden tratarse ediciones 23.1–25.1 como fuente alternativa de sus etiquetas de 2025.

Estas comparaciones son ediciones **retrospectivas del mismo fenómeno y los mismos países**, no seis observaciones experimentales independientes. Las discrepancias entre variables no equivalen a errores de uno de los archivos por defecto: cada columna representa una definición específica y las ediciones pueden corregir la codificación.

### Consecuencia operativa verificada

El requisito de la puerta futura **196 filas explícitas en la primera edición oficial completa 2027** es consistente con la cobertura histórica de todas las ediciones desde 2011. Pero **no queda garantizado** que una futura edición mantenga el mismo universo, nombres, clave de país o convención de ceros. Por eso el validador deberá comprobar cobertura, umbral, columna y procedencia **con la edición realmente publicada**, y detener el cálculo si no puede reconciliar todos los 196 GWNO. El manual no autoriza a convertir una ausencia de fila en cero.

**Resultado final:** no hay necesidad de reemitir los 196 pronósticos de ninguno de los tres modelos, ni modificar las 15 alertas. Sí hay obligación de explicitar en la web que el modelo predice **la etiqueta UCDP codificada**, no «violencia real ausente/presente» en sentido amplio.

## Reglas futuras inalteradas

- En 2027 la evaluación principal será Brier del global-only α1 menos Brier de la primera sombra LOG1P, **solo cuando exista la primera edición oficial completa y autenticada** con filas explícitas para los 196 GWNO fijos.
- Un país con un `0` oficial de muertes estatales codificadas tiene etiqueta **0 para este resultado concreto**, aunque no se pueda concluir que careció de violencia.
- Un país sin fila en la fuente **sigue sin resultado conocido**; su etiqueta no puede fabricarse como cero.
- La función de puntuación jamás debe transformarse en un detector de «cualquier violencia» sin otra definición de objetivo, fuente y emisión prospectiva nueva.

## Integridad

Se comprueba SHA-256 del GEO original (`5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5`), la sombra LOG1P (`52686923315854557a796f8f192d376dab77a4e03b14c1aeb6b4091e48104f90`), la sombra global-only (`251595a12758e006cf21dabbb9771e10b5961c469a5317d6b2b1c5de227f3697`) y las 15 alertas originales (`309b4f270e1d0d6382b7a90ae64c28d7621f96fbf3177a45aaebbffb0f958acb`). El informe `data/geo2027-ucdp-zero-coding-riskset-audit.json` se reconstruye exactamente desde cuatro fuentes oficiales antes de publicar. **No se emite ninguna predicción ni resultado 2027 nuevos.**

El proyecto IDEA LAB permanece institucional y separado de cualquier identidad o repositorio privado.
