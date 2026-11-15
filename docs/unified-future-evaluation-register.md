# Registro institucional unificado de evaluaciones futuras · 2027–2028

**Creado el 15 de noviembre de 2026.** Esta vista no añade predicciones, resultados observados, evaluaciones ni certificaciones. Es un registro **de evaluación pendiente** de las cuatro emisiones públicas originales del proyecto Psicohistoria.

## Inventario de emisiones y criterios de resolución

| Primera emisión | Preguntas | Origen→objetivo | Horizonte | Primer candidato oficial admisible | Cálculo provisional | Certificación de cobertura |
|---|---:|---|---:|---|---:|---:|
| GEO2027 | 196 | 2025→2027 | 2 años | UCDP OrganizedViolenceCY 28.1 o posterior, después de 2027 | 187/196 | **196/196 + procedencia externa** |
| NEWCONF2027 | 196 | 2025→2027 | 2 años | UCDP Multiple Onset 28.1 o posterior, después de 2027 | 187/196 | **196/196 + procedencia externa** |
| ACD2027 | 32 | 2025→2027 | 2 años | UCDP/PRIO ACD 28.1, después de 2027 | 32/32 códigos admisibles | **32/32 + procedencia y convenciones de ausencias verificadas** |
| GEO2028 | 196 | 2025→2028 | 3 años | UCDP OrganizedViolenceCY 29.1 o posterior, después de 2028 | 196/196 | **196/196 + procedencia externa** |
| **Total de preguntas emitidas** | **620** | | | | | **0 resultados futuros certificados** |

Una *pregunta* es la combinación de país, variable objetivo y año. **620 no son 620 ensayos independientes**: los países de GEO2027, NEWCONF2027 y GEO2028 coinciden en gran parte; GEO2027 y GEO2028 comparten íntegramente los 196 GWNO y el mismo año de origen 2025. ACD cubre un subconjunto de riesgo de 32 países; tampoco es otra evaluación del mismo concepto que NEWCONF.

**No puede agregarse un Brier entre variables distintas** para proclamar que un modelo predice mejor el conjunto de la violencia geopolítica. La comparación de modelos debe ser emparejada dentro de cada emisión y conservar la definición inicial del resultado. Un único año objetivo produce una sola realización de un sistema con posibles shocks compartidos; no autoriza p-valores IID.

## Qué significa el mínimo provisional

Los evaluadores futuros GEO2027 y NEWCONF2027, programados previamente, permiten ofrecer resultados **exploratorios** al cubrir un mínimo del 95 % de la cohorte original (187/196), pero ese cálculo puede sufrir sesgos importantes de cobertura y **no equivale a una certificación**. Para declarar una evaluación oficial completa se exige cubrir los 196 GWNO originales y autenticar de forma independiente la primera edición anual completa.

ACD2027 requiere evidencia de codificación de los 32 GWNO elegibles, el tratamiento de ausencias y una edición sin filas objetivo ambiguas. GEO2028 es más estricto desde el principio: **no puntúa provisionalmente con 195/196**.

No se han ejecutado evaluaciones futuras ni se han certificado etiquetas: los cuatro registros mantienen valores **0** en los campos de resultados, scores y habilidad demostrada. Sus algoritmos de puntuación no pueden autocertificar que el operador haya aportado realmente la *primera edición oficial completa*. Un hash SHA-256 prueba qué archivo se ha utilizado, no quién lo ha publicado ni cuándo.

## Comparación por variable (no mezclar)

- **GEO2027:** violencia organizada *estatal*, 25 o más muertes anuales en 2027. Modelo principal Markov país a dos pasos contra referencia global 2021–2025; Markov global es comparador secundario.
- **NEWCONF2027:** ANY(newconf=1) por país durante 2027, agregado de múltiples episodios intraestatales. Modelo principal de nuevos conflictos contra baseline global; no es idéntico a un conflicto activo.
- **ACD2027:** persistencia de cualquier conflicto intraestatal tipo 3/4 en 2027 entre los **32 países activos en origen 2025**. Modelo primario p_global_recent5, comparaciones país EB y grupo lag1 exploratorias.
- **GEO2028:** misma variable binaria que GEO2027, **pero resultado 2028** desde el mismo origen 2025, Markov país a tres pasos contra baseline global; comparador Markov global tres pasos. No supone una nueva edición de origen 2026 ni una réplica temporal independiente.

Las fechas de primera emisión son las de GitHub (10, 11 y 12 de noviembre de 2026 para las cohortes 2027, y 15 de noviembre de 2026 para GEO2028), verificadas por su primer commit y SHA congelado. **No son una notarización temporal externa.**

## Auditoría nueva y corrección de una puerta temporal

La auditoría transversal scripts/build_future_evaluation_contract_registry.py **reutiliza los cuatro evaluadores reales**, los cinco originales documentales de 2027 y el manifiesto/archivo GEO2028. Falla si cambian los SHA, las tasas de cobertura, el año objetivo, el horizonte, el modelo primario, la procedencia de la primera emisión o la prohibición de marcar resultados futuros inexistentes.

Se ha corregido adicionalmente scripts/evaluate_2027_official.py: la puerta de entrada GEO2027 ya no acepta una URL antigua **UCDP 26.1 o 27.1** acompañada de una fecha declarada ficticia de 2028. Requiere una ruta exacta UCDP OrganizedViolenceCY de edición al menos **28.1**, al igual que los evaluadores de NEWCONF y ACD2027 tienen sus propias versiones mínimas. Esto evita etiquetar como prospectivo un archivo viejo.

El informe derivado de las fuentes data/future-evaluation-contracts.json se congela byte a byte y se reproduce en el job obligatorio unified_future_evaluation_contracts. La vista pública es src/future-evaluation-register.mjs, con pruebas de integridad sobre todos los archivos ya emitidos, ataque de inyección HTML, alteración de fecha, invento de resultados y cambio de denominador. No se guardan ni descargan etiquetas oficiales futuras.

## Corrección estadística posterior (PR #80)

Los evaluadores GEO2027 y NEWCONF2027 **ya no calculan intervalos bootstrap IID por países**. Se han retirado las funciones de remuestreo y se han sustituido por **cotas algebraicas exactas del Brier de la cohorte original de 196 países** cuando faltan etiquetas. Las cotas recorren todas las asignaciones posibles de 0/1 a los países sin resultado; **no son intervalos de confianza** y no permiten afirmar superioridad estadística.

Las métricas exploratorias basadas en 187–195 países resueltos siguen siendo descriptivas y deben diferenciarse de la puntuación completa de 196. No se han cambiado las predicciones emitidas ni las condiciones de procedencia independiente de futuras fuentes. Véase docs/non-iid-2027-evaluation-guards.md para la demostración y las nuevas pruebas.

**Criterio de éxito futuro:** conjuntos de etiquetas verificados y completos, fuentes primarias trazables, cálculo con probabilidades emitidas sin reajuste, separación estricta de endpoints y un análisis de la dependencia temporal/geográfica con la incertidumbre correctamente expresada. Hoy: **cuatro emisiones reales, 620 preguntas emitidas, cero resultados futuros certificados y ninguna habilidad prospectiva demostrada.**
