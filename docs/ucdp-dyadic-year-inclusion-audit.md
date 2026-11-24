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
