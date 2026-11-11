# GEO-2027 — Diagnóstico histórico de dispersión de recuentos de transiciones

**11 de noviembre de 2026.** Investigación complementaria a las 15 alertas prospectivas, sin incorporar observaciones de 2027, sin alterar pronósticos y sin estimar correlaciones entre países a partir de hipótesis arbitrarias.

## La pregunta que realmente permiten responder los datos

El modelo Markov GEO publica probabilidades de cambio para cada país. Suponer independencia para calcular el número total de cambios introduce una hipótesis conjunta no estimada. Un paso empírico previo consiste en analizar, con datos históricos, cuánto difieren los **recuentos anuales observados** de los esperados bajo la misma receta de probabilidades.

La presente investigación no pretende inferir todavía una «correlación geopolítica» única. **Un exceso de dispersión puede deberse tanto a dependencia real como a mala calibración de los riesgos marginales, cambios de régimen, errores de fuente, cobertura o revisiones.**

## Dos bloques, explícitamente distintos

**A. Referencia histórica revisada de 12 años (2012–2023).** A partir de la edición UCDP OrganizedViolenceCY **26.1**, SHA-256 `66910888f5653af42776d2debc1d72fe527559e7f7fc82e69b7c8771467f2d34`, se reconstruye en cada origen `t−2` el modelo original de Markov con entrenamiento solo hasta ese origen y etiqueta posterior `t`. Se separan los países con indicador inicial 0 y 1 y se calculan los cambios 0→1 y 1→0. **Limitación decisiva:** las etiquetas históricas proceden de una única edición revisada publicada en 2026, no de las ediciones disponibles realmente en cada año de origen. Este bloque es *ex post*; 12 años con solapamiento de horizontes y repetición de países no son 12 pruebas independientes de predicción.

**B. Comprobación separada por edición de 2 años (2024–2025).** Se reutilizan exactamente las dos cohortes oficiales y hashes del estudio de atribución GEO-2027: **23.1 origen 2022 → 25.1 resultado 2024** y **24.1 origen 2023 → 26.1 resultado 2025**, con 196 países y 69 casos de estado activo entre 392 observaciones. El algoritmo no recibe las etiquetas de la fuente posterior durante el entrenamiento. Dos años son insuficientes para identificar estructuralmente covarianzas, pero sirven como prueba adicional de estabilidad del diagnóstico de recuentos con etiquetas de ediciones distintas.

> Los dos bloques son comparaciones retrospectivas. El B es más fuerte frente a revisiones ex post de la etiqueta, pero tampoco posee emisión histórica fehaciente de los pronósticos.

## Métrica y cálculo

Para cada año objetivo `t` y cada conjunto conocido en origen `s∈{0,1}`, se fija la probabilidad de transición `q_it = p_model` para entrada y `q_it = 1−p_model` para resolución. Definimos:

\[
K_{t,s}=\sum_i \mathbf{1}(Y_{i,t}\neq s),\quad E_{t,s}=\sum_i q_{i,t},\quad V_{t,s}^{\mathrm{ind}}=\sum_i q_{i,t}(1-q_{i,t}).
\]

El residual anual estandarizado es `Z=(K−E)/√V_ind`, y la «razón de dispersión de recuentos» se calcula como media aritmética por año del `Z²`, manteniendo los grupos 0 y 1 separados. También se compara el valor de la misma estadística usando el **Markov global** ya fijado; ambos modelos puntúan exactamente los mismos países-año.

Si la marginal estuviera bien calibrada, y además los países fueran condicionalmente independientes, el cuadrado medio de estos residuales sería aproximadamente 1. Pero **un valor mayor que 1 no implica automáticamente correlaciones positivas** ni puede traducirse sin más a un parámetro de mezcla común `w`. Un valor menor que 1 tampoco demostraría independencia.

Solo se publican agregados año×estado (n, E, K, V, residuales) y totales. No se extraen identificadores de países ni se trasladan datos futuros a 2027.

## Condiciones de integridad

- UCDP 26.1 verificada por SHA-256, con esquema y fuente oficial.
- Cuatro ediciones UCDP históricas verificadas por hash ya archivado; objetivo 2024/2025 separado de la versión que genera los pronósticos de origen.
- Cohortes y rangos temporales fijos 2012–2023 vs 2024/2025, 392 observaciones y 69 positivos externos, mismo horizonte de dos años y ninguna selección de hiperparámetros.
- Pruebas sintéticas de recuentos, dispersión, comparadores, etiquetas ausentes, duplicados y fuentes corruptas.
- Ningún resultado 2027 observado; ninguna validación prospectiva de independencia o dependencia.
- El informe reproducible queda protegido por CI y, tras su primera ejecución válida, archivado byte a byte.

**Decisión científica prevista:** no ajustar el peso de dependencia de las 15 alertas GEO-2027 con estas muestras: sería introducir hipótesis oportunistas dependientes de datos revisados y de muy pocos años externos. El siguiente paso confirmatorio requeriría más ediciones independientes fechadas al origen o una cohorte futura completa.
