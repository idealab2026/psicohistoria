# GEO2027 y NEWCONF2027: límites exactos de dependencia entre países

**Estudio de 13 de noviembre de 2026, previo a resultados 2027.** Sensibilidad matemática, no estimación de correlación ni capacidad predictiva demostrada. Las **424 preguntas país × variable** de las tres cohortes se mantienen sin alterar y no se ha observado ninguna etiqueta de 2027.

## Objeto del estudio y variables objetivo

| Cohorte | Países | Variable 2027 | Comparaciones |
|---|---:|---|---|
| GEO2027 | 196 | Violencia organizada estatal de al menos 25 muertes anuales | Principal p_model vs p_global_markov y shadow calibrado |
| NEWCONF2027 | 196 | Al menos un nuevo episodio de conflicto intraestatal por país, ANY(newconf=1) | Principal p_model vs p_baseline_global_5y |

Se calcula también GEO p_model frente al campo original p_baseline_global_5y **solo como diagnóstico de archivo**: no está preregistrado en el registro de 2027 como comparador oficial adicional.

**No se suman las puntuaciones Brier de GEO y NEWCONF**, que tienen resultados definidos de manera distinta y comparten países/año. La cohorte ACD2027 es otra variable con solo 32 países. Las 15 alertas y el shadow GEO no añaden observaciones independientes.

## Matemática exacta sin asumir independencia real

Para el modelo principal p_i y comparador q_i del **mismo** endpoint, el diferencial Brier es

\[
D = \frac{1}{196}\sum_{i=1}^{196}[(q_i-Y_i)^2-(p_i-Y_i)^2]
  =c+\sum_i a_iY_i,\qquad a_i=-\frac{2(q_i-p_i)}{196}.
\]

D positivo favorece al principal y negativo al comparador. Se plantean dos mundos **contrafactuales** separados: las probabilidades verdaderas de Y son las p_i o bien las q_i. No se sabe si alguno es correcto. En cualquiera de ellos, la esperanza de D es positiva o negativa, respectivamente, con magnitud igual a la media de los cuadrados de diferencias de probabilidades, independientemente de las correlaciones.

Con probabilidades marginales fijadas r_i, la varianza de D suponiendo Bernoulli **independientes** sería suma de a_i² r_i(1−r_i). La **máxima varianza alcanzable** bajo cualquier dependencia conjunta con esas mismas r_i se obtiene con una uniforme U común: Y_i=1[U<r_i] si a_i≥0, y Y_i=1[U>1−r_i] si a_i<0. Los términos ponderados quedan comonótonos, alcanzando simultáneamente las cotas de Fréchet en las covarianzas. Esta cota es **exacta**; no se está estimando una correlación geopolítica. La independencia tampoco constituye una cota inferior general.

## Resultados si las marginales del modelo principal fueran las verdaderas

| Comparación (secundario − principal) | E[D] hipotética | SD independencia | SD máxima | Multiplicador de varianza |
|---|---:|---:|---:|---:|
| GEO Markov | +0,00376352 | 0,00302875 | 0,01579073 | **27,18×** |
| GEO shadow | +0,00193505 | 0,00266903 | 0,01532548 | **32,97×** |
| GEO baseline global (solo diagnóstico) | +0,08205818 | 0,01455052 | 0,09292246 | **40,78×** |
| NEWCONF baseline global | +0,00039052 | 0,00068328 | 0,00322907 | **22,33×** |

SD es la desviación típica de la **diferencia Brier entre modelos**, no la del riesgo de un país. Un multiplicador de varianza de 32,97 equivale a multiplicar la SD por su raíz, aproximadamente 5,74. Las métricas entre endpoints no se pueden utilizar para comparar qué proyecto predice mejor.

## Resultados si las marginales del comparador fueran las verdaderas

| Comparación | E[D] hipotética | SD independencia | SD máxima | Multiplicador de varianza |
|---|---:|---:|---:|---:|
| GEO Markov | −0,00376352 | 0,00310095 | 0,01918456 | **38,27×** |
| GEO shadow | −0,00193505 | 0,00217648 | 0,01270354 | **34,07×** |
| GEO baseline global (diagnóstico) | −0,08205818 | 0,01559009 | 0,13004001 | **69,58×** |
| NEWCONF baseline global | −0,00039052 | 0,00023750 | 0,00151280 | **40,57×** |

El signo del Brier esperado cambia porque este segundo mundo **supone verdaderas otras probabilidades**. No es una predicción sobre cuál será el modelo mejor ni sobre la probabilidad real de que gane.

## Dónde discrepan las probabilidades originales

- GEO principal/Markov: **Burundi** aporta 7,66 % de la suma de brechas cuadráticas; después Senegal y Colombia.
- GEO principal/shadow: **Haití** aporta 7,09 %; después Níger y Angola.
- NEWCONF principal/baseline: **Malí** aporta 13,22 %; después Somalia y Siria.
- GEO principal/baseline global como diagnóstico no preregistrado: Colombia, Irak y Afganistán empatan con 3,20 % cada uno.

Esto mide discrepancia entre vectores de modelos, **no relevancia geopolítica, causalidad o probabilidad real de conflicto**.

## Interpretación científica y límites

Bajo unas probabilidades marginales hipotéticamente correctas, la independencia podría subestimar sustancialmente la varianza del diferencial Brier con respecto a otras distribuciones conjuntas igualmente compatibles. Los 196 países nominales no son automáticamente 196 experimentos independientes. El mismo razonamiento afecta a los 424 registros de las tres cohortes: contienen países compartidos y distintas variables objetivo.

**No se ha estimado** la covarianza real entre países, entre endpoints o entre años. Los mundos de dependencia son contrafactuales, no intervalos de confianza, p-valores ni métricas de desempeño observadas. Tampoco conocemos las distribuciones conjuntas reales de 2027. Los comparadores exploratorios conservan su condición, y la superioridad generalizable solo podrá estudiarse con nuevos años objetivo emitidos antes de observar resultados oficiales, validaciones por bloques temporales y países, y definiciones fijas.

## Trazabilidad

El script scripts/diagnose_geo_newconf2027_sharp_dependence.py autentica los cinco archivos y manifiestos de emisión original, reproduce el registro de 424 preguntas y calcula separadamente las cotas exactas. El archivo data/geo-newconf2027-sharp-dependence.json congela los resultados y se compara byte a byte en el job institucional geo_newconf2027_sharp_dependence. Las pruebas scripts/test_diagnose_geo_newconf2027_sharp_dependence.py incluyen máximos de Fréchet de signos opuestos, 196× de multiplicador de varianza para un caso sintético de shock común, modelo degenerado y rechazo de alteraciones y datos inválidos.

**Ninguna etiqueta futura, archivo original emitido, probabilidad o elección de modelo principal se ha modificado.**
