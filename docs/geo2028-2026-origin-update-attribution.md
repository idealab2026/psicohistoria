# GEO2028 — Descomposición preregistrada de actualización 2025→2026

**Pre-registro del 15 de noviembre de 2026.** UCDP OrganizedViolenceCY 27.1 con año completo 2026 **todavía no existe públicamente**. Este protocolo no emite pronósticos nuevos ni registra resultados reales 2028. Las **620 preguntas emitidas** en las cohortes previas se mantienen intactas.

## Problema científico

Al comparar la primera emisión GEO2028 (origen 2025; UCDP 26.1; horizonte tres años) con la futura GEO2028 de origen 2026 (UCDP 27.1; horizonte dos años), no debe imputarse todo cambio de probabilidad a la información del año 2026. El archivo 27.1 puede haber revisado datos de 2025 y anteriores, y al estimar tasas globales pueden cambiar los países que participan en el entrenamiento.

## Cuatro etapas del mismo pronóstico objetivo 2028

| Etapa | Modelo / fuente | Significado |
|---|---|---|
| **A** | Primera emisión real de 2026: origen 2025, horizonte tres años, fuente 26.1, SHA congelado | Pronóstico GEO2028 original inalterable |
| **B** | Reestimar a origen 2025/horizonte tres con datos de la futura fuente 27.1 **truncados en 2025** | Aísla el cambio por revisión histórica, incluidos parámetros globales y población de entrenamiento |
| **C** | Mantener **congelado** el kernel Markov de B, observar el estado oficial 2026, proyectar dos pasos hasta 2028 | Aísla la sorpresa de observar 2026 respecto al estado esperado |
| **D** | Reestimar el mismo kernel Markov con todas las transiciones disponibles **hasta 2026** y proyectar dos pasos a 2028 | Candidato de emisión futura 2026→2028 |

Para cada país GWNO comparable en las tres poblaciones, el desglose algebraico exacto es:

\[
p_D-p_A=(p_B-p_A)+(p_C-p_B)+(p_D-p_C).
\]

Las etiquetas de las componentes son, respectivamente, *cambio de fuente/vintage y composición*, *sorpresa del estado observado 2026*, y *reajuste del kernel con transiciones de 2026*. Es un **desglose secuencial y dependiente del orden**, no tres efectos causales ni tres contribuciones estadísticamente independientes.

### Control de consistencia Markov

Si Q es el kernel de 2025 ajustado en el archivo 27.1, el estado 2025 es y25, el observado en 2026 es y26, y g(s) la probabilidad de estado activo a dos pasos desde el estado s, entonces:

\[
\pi=\Pr_Q(Y_{2026}=1\mid Y_{2025}=y25),\qquad
p_B=(1-\pi)g(0)+\pi g(1),
\]
\[
p_C-p_B=(y26-\pi)(g(1)-g(0)).
\]

Estas identidades **deben pasar en cada país**. Evitan errores de horizonte, la confusión entre estado inicial y resultado futuro y la utilización indebida de una fuente posterior a 2026.

### Comparador de prevalencia global

La referencia global de cinco años no se comporta como el modelo de Markov. Por eso se reportan separadamente sus componentes: la diferencia de la prevalencia 2021–2025 entre la fuente 26.1 y la futura 27.1 truncada a 2025, y el posterior desplazamiento de la ventana a 2022–2026. No se atribuye el cambio de esa referencia a una inexistente *sorpresa de estado por país*.

## Países comparables, fuente y límites

El análisis solo compara los GWNO presentes en la emisión original de 2025, la población reconstruida de 2025 en 27.1 y la población de origen 2026 en 27.1. Identifica países incorporados, ausentes y cambios de la etiqueta oficial 2025. Se requieren al menos **180 países comparables**; si el universo resulta inestable, no se fuerza una comparación.

El ejecutable **scripts/decompose_geo2028_origin2026_update.py** usa exclusivamente la fuente anual 27.1 y el manifiesto de SHA definidos previamente en **docs/geo2028-origin2026-preregistration.md**. Su CLI exige original GEO2028 2025–2028 autenticada con SHA-256 fijo **fd5832c6896548b053202f2f84bd0f7cd4a75df44462fbd4f259b9d8d4c39bde** y comprueba que la nueva predicción D coincida exactamente con el generador preregistrado para origen 2026.

- No acepta datos oficiales anteriores a la disponibilidad real de un año 2026 completo ni datos posteriores a 2026 como variables de origen.
- No altera ninguna primera emisión 2027 o 2028 ni permite escribir un candidato dentro del repositorio.
- No produce inferencia de correlación, intervalos de confianza IID, efectos causales ni afirmaciones de habilidad predictiva validada.
- La fecha y hash introducidos por un operador son comprobaciones de coherencia, **no** acreditaciones independientes de la fecha de primera publicación UCDP.
- El target compartido 2028 impide tratar las emisiones H3 desde 2025 y H2 desde 2026 como experimentos estadísticamente independientes.

## Evidencia de calidad antes de publicar números

La CI institucional ejecuta únicamente **datos sintéticos**, para comprobar: (i) identidad Markov de estado condicional, (ii) suma exacta A→D por país, (iii) ausencia de cambio de fuente cuando no hay revisiones, (iv) detección de revisiones históricas 2025, (v) entrada/salida de países, (vi) rechazo de modificaciones de probabilidades o futuros resultados 2027/2028, (vii) trazabilidad de baseline y denominadores de países realmente comparables.

**Estado real: no se dispone de edición oficial anual 27.1, de probabilidades emitidas con origen 2026 ni de resultados certificados 2028.** Esta investigación preregistra *cómo interpretar* el cambio cuando la fuente exista, en vez de improvisar la atribución después de observar los números.
