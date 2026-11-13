# ACD2027 · Discriminación prospectiva exacta, condicionada al número de países con conflicto

**Emisión del análisis:** 13 de noviembre de 2026, **antes de observar resultados de 2027**. La evidencia es matemática e hipotética, NO es una cuarta cohorte de pronóstico, NO utiliza etiquetas 2027 y NO sustituye las tres probabilidades originales de los 32 países ACD2027.

## Pregunta

¿Cuánta información aportará la futura observación del número de países con conflicto intraestatal UCDP/PRIO ACD (tipo 3/4) durante 2027, y cuándo será imprescindible conocer cuáles son esos países para decidir qué modelo tuvo mejor Brier?

Modelos publicados y congelados: primario **p_global_recent5**, comparadores secundarios exploratorios **p_lag1_group** y **p_country_eb**. Riesgo: solo los **32 países activos en ACD de 2025**; no inventar los ceros de países no pertenecientes a la cohorte. En 2026 existen **0 resultados observados de 2027**.

## Derivación exacta sin suponer independencia

Para cualquier país i, p_i es la probabilidad primaria y q_i la del comparador; y_i pertenece a {0,1}. La diferencia de pérdida Brier del secundario menos el primario es

\[
d_i(y_i)=(q_i-y_i)^2-(p_i-y_i)^2
       =q_i^2-p_i^2-2(q_i-p_i)y_i.
\]

La diferencia media total es la suma de esos 32 términos dividida por 32. Para un número hipotético K de países con conflicto en 2027, imponemos **exactamente** que la suma de los y_i sea K.

El extremo **mínimo** se alcanza asignando y_i=1 a los K países cuyos incrementos \(-2(q_i-p_i)\) sean los menores. El extremo **máximo** se alcanza asignando y_i=1 a los K países cuyos incrementos sean los mayores. Por tanto, los dos límites son **exactos y realizables**; se conservan códigos GWNO de testigos para auditar ambas asignaciones. El procedimiento ordena los 32 incrementos: **no** trata las 2^32 posibles combinaciones como escenarios equiprobables ni introduce independencia entre países.

**Signos:** diferencia secundaria−primaria negativa = ganó secundario; positiva = ganó primario. Si todo el intervalo queda del mismo lado de cero, K determina el ganador. Si el intervalo cruza cero, conocer K NO basta: importan los países concretos.

## Resultados comprobados con primeras emisiones inalteradas

| Comparador | K que garantiza victoria secundaria | K que garantiza victoria primaria | K con identidad de países decisiva |
|---|---|---|---|
| **lag1** | **0–19** | **32** | **20–31** |
| **country-EB** | **0–1** | **32** | **2–31** |

Son límites sobre **cuentas hipotéticas**, no pronósticos de cuántos países tendrán conflictos. Por ejemplo, si K=27, para lag1−global hay resultados binarios posibles con diferencias tan bajas como **−0,01337366** y tan altas como **+0,00549579**. Ni un recuento agregado de 27 países ni su suma de probabilidades serían suficientes para certificar qué modelo obtuvo menor Brier.

La segunda comparación es todavía más heterogénea: con K=27, country-EB−global tiene un intervalo alcanzable de **−0,03469696 a +0,03766331**. Los 32 registros por país, su procedencia y su cobertura anual son esenciales.

## Distancia entre modelos y potencia conceptual

Un contraste **condicionado a hipótesis explícitas de probabilidades marginales verdaderas** proporciona una escala de diferencias esperables en pérdida media:

\[
E[\operatorname{Brier}(q)-\operatorname{Brier}(p)]
=\begin{cases}
+\frac{1}{32}\sum_i(q_i-p_i)^2, & \text{si los }p_i\text{ son marginales verdaderas},\\
-\frac{1}{32}\sum_i(q_i-p_i)^2, & \text{si los }q_i\text{ son marginales verdaderas}.
\end{cases}
\]

Esta identidad depende únicamente de la **linealidad de la esperanza**, no de que los países sean independientes. **No** proporciona error estándar, p-valor, frecuencia de victoria o capacidad predictiva validada.

| Comparación | Distancia cuadrática media entre probabilidades | Mayor aportante |
|---|---:|---|
| lag1 frente a global | **0,00318378** | Sudán del Sur: **96,21 %** |
| country-EB frente a global | **0,00624061** | Haití: **15,43 %** |

En lag1, casi toda la diferencia entre vectores se concentra en el único país de los 32 que no estuvo activo en 2024, Sudán del Sur. Es una medida de **discrepancia entre modelos**, no de importancia geopolítica ni probabilidad de conflicto.

## Protocolo de evidencia prospectiva y decisión

1. **Antes de conocer 2027:** mantener inmutables origen 2025, 32 GWNO, probabilidades, fechas y SHA originales. Este informe es derivado, separado de la emisión. Registrar de antemano Brier medio completo como comparación principal; log-loss como comparación secundaria ya prevista en el evaluador oficial.
2. **Una vez publicada la primera edición oficial anual completa:** ejecutar exclusivamente el contrato de resolución ya existente (scripts/evaluate_acd2027_retention_official.py), previa certificación independiente de autenticidad, primera fecha, cobertura y equivalencia de país. **No convertir una ausencia o recodificación dudosa en etiqueta cero**; si falta cobertura, bloquear puntuación.
3. **Con etiquetas admisibles:** informar el Brier primario, los dos diferenciales frente a primario y los 32 países originales. El evaluador oficial ahora **comprueba automáticamente** que cada diferencia Brier pertenece al intervalo exacto predefinido para su K, y rechaza resultados contradictorios. Si el resultado real no pertenece, hay corrupción de datos, falta de integridad o una discrepancia de definiciones. Se informa expresamente que la puntuación candidata no autoriza cambiar de modelo.
4. **Después de un único año:** informar resultados descriptivos y sensibilidad por país, sin contrastes IID entre países, sin alegar significación generalizable y **sin cambiar automáticamente de modelo**.
5. **Para generalizar:** cualquier nuevo año objetivo debe disponer de probabilidades nuevas emitidas **antes** del conocimiento de sus etiquetas oficiales, con endpoint, denominador y tiempos auditados. Contrastar distintos bloques de años objetivo, persistencia de la ventaja al excluir años y países y dependencia temporal. No juntar Brier de GEO, NEWCONF y ACD como si fueran la misma tarea. No se atribuirá superioridad validada por elegir un umbral arbitrario de número de años o por un solo acierto.

Esta investigación complementa la auditoría ya publicada de **137 evaluaciones históricas, 42 países y los 32 países de la cohorte ACD2027**, cuya muestra histórica revela sesgo de representatividad y ventaja de lag1 que se invierte en los países actualmente emitidos. Ningún resultado de este informe altera la selección original del modelo primario.

## Reproducción y pruebas

- scripts/diagnose_acd2027_exact_count_evidence.py: autenticación de los cinco archivos de emisión y 424 preguntas país–endpoint; cálculo algebraico de 33 límites de K por cada comparador; guarda testigos GWNO de cada extremo.
- data/acd2027-exact-count-evidence.json: informe congelado con **ambos intervalos exactos para cada K de 0 a 32**. Su reproducción se verifica byte a byte en CI.
- scripts/test_diagnose_acd2027_exact_count_evidence.py: enumeración bruta controlada de un subconjunto sintético de cuatro países diferenciales para validar cada K, alteraciones de la cohorte, valores inválidos y prueba de esperanza bajo **dependencia perfecta**.
- Job obligatorio de GitHub Actions acd2027_exact_count_evidence, sin descargar ni inspeccionar ningún resultado 2027.

**Limitación científica:** conocer fronteras exactas y diferencias cuadráticas entre pronósticos todavía no identifica cuál está calibrado, ni permite estimar cuál ganará o si 2027 contará con datos oficiales suficientes. Los datos ACD representan presencia registrada de conflicto intraestatal, NO ausencia de cualquier violencia ni paz.
