# GEO2027 · Frontera exploratoria de precisión histórica y estabilidad editorial

**Protocolo fijo del 16/11/2026.** Este estudio se añade a las auditorías del modelo continuo LOG1P de PSICOHISTORIA; **ninguna predicción existente se reemite o modifica**. No estamos construyendo retrospectivamente un nuevo «campeón» con datos que ya hemos inspeccionado.

## Pregunta específica y candidatos predefinidos

La auditoría anterior detectó que una corrección de **0 a 10 muertes de violencia estatal** en el año de origen puede aumentar la probabilidad de algunos países en **casi 19 puntos porcentuales**, aunque ambos conteos sean inferiores al umbral binario de 25. La pregunta es cuantificar el compromiso entre **sensibilidad de la pendiente inactiva** y **error predictivo retrospectivo**.

La sombra LOG1P utiliza:

\[
\operatorname{logit} p = \operatorname{logit}p_{\rm GEO}+\beta_0
+\beta_I x_I(d)+\beta_A x_A(d).
\]

En esta nueva ablación **se reduce exclusivamente la pendiente para países originalmente inactivos** con un multiplicador \(\alpha\):

\[
\operatorname{logit}p_\alpha =
\operatorname{logit}p_{\rm GEO}+\beta_0+
\alpha\beta_I x_I(d)+\beta_A x_A(d).
\]

Las **cinco** alternativas del diagnóstico quedan registradas desde el principio:
\[
\alpha\in\{0,0{,}25,0{,}50,0{,}75,1\}.
\]

- \(\alpha=1\): sombra original LOG1P, **SHA-256 inmutable** \`52686923315854557a796f8f192d376dab77a4e03b14c1aeb6b4091e48104f90\`.
- \(\alpha=0\): desactivar la señal continua de muertes **solo en países con menos de 25**; no es igual al modelo calibrado solo-intercepto en los activos, que conservan \(\beta_A\).
- Los valores intermedios reducen la intensidad de esa señal sin afectar la originalidad de la emisión, los países activos ni la probabilidad en el caso particular de cero muertes **observadas**. La sensibilidad *ante revisar cero a un número positivo* sí se atenúa.
- **Todos los alfas son intervenciones post-emisión**, no nuevos pronósticos prospectivos. Las salidas para 2027 se guardan en un archivo **de investigación**, no en el registro de emisiones.

Es una ablación de una sola dimensión, no una búsqueda general por mejores formas funcionales ni un reentrenamiento penalizado del parámetro. Se conservan el intercepto y el coeficiente de países activos aprendidos en los estudios anteriores, con el Markov binario como offset.

## Dos ejes y tres cortes temporales diferenciados

1. **Validación interna 2018–2020:** los coeficientes de la familia LOG1P proceden de 2012–2017 de cada edición de origen, con la penalización ya seleccionada con la regla publicada. Se recalcula Brier/log-loss para los cinco alfas sobre los mismos países y años de desarrollo. Ese mismo tramo ya participó en la selección de regularización, por lo que **tampoco es confirmatorio** para elegir una variante.
2. **Resultados históricos externos 2024 y 2025:** se reutilizan los pares UCDP oficiales y separados por edición, origen **23.1 hasta 2022 → 25.1 en 2024** y **24.1 hasta 2023 → 26.1 en 2025**. Cada coeficiente base es el mismo ya reproducido para la familia LOG1P, ajustado sin ninguna etiqueta posterior al origen. Se exige coincidencia con el Brier y log-loss publicados para \(\alpha=1\). Como esos resultados **ya se examinaron en iteraciones previas del laboratorio**, cualquier cambio de Brier es **exploratorio** y NO demuestra superioridad independiente.
3. **Estrés de la emisión real 2027:** usando las **196 probabilidades publicadas** de la sombra de 2027, su **origen 2025**, sus coeficientes ya emitidos y el Markov original inmutable, se calculan **extremos hipotéticos de ±10 muertes estatales best** por país, recortados para no cambiar el estado binario. Se reproduce exactamente el informe de estrés previo cuando \(\alpha=1\). Se reportan anchura media, mediana, P95 y máxima, número de países con posible cambio ≥5 pp y qué miembros del top-10 de entrada/top-5 de resolución de la **sombra simulada** son obligatorios/posibles frente a todas las perturbaciones del escenario.

## Resultados reproducidos: no existe «campeón» entre los cinco puntos

El reporte completo fue obtenido con las cuatro ediciones oficiales SHA-fijadas, con la misma cohorte GEO de 196 países en dos años objetivo (392 casos). En **α=1**, tanto el Brier histórico como las bandas y rankings del informe emitido de 2027 coinciden con sus estudios originales. **Todas las variantes alteradas α<1 son contrafactuales de investigación y no han sido emitidas.**

| Multiplicador de pendiente inactiva | Brier 2024 | Brier 2025 | Brier conjunto (2024–25) | Anchura media escenario 2025 ±10 muertes (pp) | Top-10 hipotético entrada, puestos obligatorios |
|---|---:|---:|---:|---:|---:|
| **α=0** | 0,039480 | **0,036149** | 0,037815 | **0,0815** | **10/10** |
| α=0,25 | 0,039091 | 0,036220 | 0,037655 | 0,6577 | 6/10 |
| α=0,50 | 0,038684 | 0,036339 | 0,037512 | 1,3532 | 5/10 |
| α=0,75 | 0,038293 | 0,036531 | 0,037412 | 2,1868 | 3/10 |
| **α=1**, sombra emitida | **0,037960** | 0,036827 | **0,037393** | 3,1780 | 2/10 |

**Intercambio cuantitativo:** α=0 reduce la anchura media hipotética aproximadamente **97,4 %** con respecto a α=1, mientras que el Brier histórico conjunto empeora solo **1,1 % relativo** (diferencia absoluta de **+0,000421**). La menor sensibilidad no es gratuita en el score conjunto, aunque el coste en estos dos años parezca moderado.

**Heterogeneidad temporal decisiva:** el Brier de **2024** disminuye monótonamente al aumentar α y favorece **α=1**; el de **2025** mejora monótonamente al reducirlo y favorece **α=0**. El Brier de validación interna **2018–2020**, acumulado sobre dos ediciones correlacionadas, favorece igualmente α=1 (**0,039367** frente a **0,040616** para α=0); tampoco es una prueba independiente, pues ese mismo periodo se utilizó previamente para seleccionar la regularización de LOG1P. **Ninguno de esos años debe convertirse ahora en una nueva regla de selección α.**

### Qué ocurriría con la emisión prospectiva —sin reemplazarla

Las probabilidades reales emitidas con α=1 tienen una suma de **35,9840** países activos esperados. El cálculo puramente contrafactual con α=0 daría **35,3795**, una diferencia de −0,6045 países esperados. En 2025, **154 de los 162 países inactivos parten de exactamente cero muertes**: para ellos, la *probabilidad central* calculada no cambia con α, pero sí desaparece la exposición del predictor a posibles revisiones de cero a valores positivos dentro de 0–24. Para los otros ocho inactivos con muertes positivas, α sí afecta a la probabilidad central.

En el caso de **Burundi** (d=0 en 2025), el salto hipotético al revisar 0→10 muertes se reduce de **+18,5354 puntos** en la sombra α=1 a **cero puntos** en la contrafactual α=0, sin alterar el offset Markov. El máximo ancho de los 196 países en α=0 sigue siendo **3,2058 pp** por los países **activos**, cuya pendiente no hemos tocado. Así se evita presentar α=0 como insensible a *toda* revisión histórica: la robustez certificada es parcial y condicional.

En rankings contrafactuales del grupo **162 inactivos** bajo ±10, el top-10 tiene **10 puestos obligatorios de 10** con α=0 y **2 puestos obligatorios** con α=1. Sin embargo, el grupo de **34 activos** retiene solo **3/5 miembros obligatorios del top-5** para *todos* los valores de α, porque la pendiente activa se mantiene fija. Son rankings *de la familia de sombras*, no las 15 alertas originales, que continúan intactas y con sus SHA.

**Los cinco puntos resultan no dominados** sobre los dos ejes concretos (Brier reutilizado y anchura hipotética), porque bajar α mejora la estabilidad y subirlo mejora el Brier histórico conjunto. Por tanto, **no seleccionamos ni reemitimos un modelo ganador**. La comparativa no es un experimento aleatorizado de revisiones UCDP, no estima cobertura de incertidumbre ni justifica cambiar a posteriori la primera emisión 2027.

El siguiente contraste científicamente limpio es **evaluar las predicciones actualmente emitidas con el resultado oficial futuro de 2027**, sin modificarlas. Las variantes α<1 podrán informar diseño de hipótesis nuevas pero, si algún día se emiten, requerirán archivo, fecha pública, identificador y evaluación prospectiva propios.

## Interpretación y decisión metodológica

Se dibuja una **frontera de Pareto descriptiva** de cinco puntos sobre (i) Brier agregado histórico 2024–2025 **ya observado** y (ii) anchura media de banda hipotética de ±10 muertes para la emisión 2027, **no una distribución estadística de revisión**. Un alfa es *dominado* si otro es igual o mejor en ambos ejes y estrictamente mejor en al menos uno. Es una herramienta de diagnóstico, **no un algoritmo de selección de un modelo ganador** ni una prueba estadística.

Una mejora de robustez trivial al disminuir \(\alpha\) no demuestra que la nueva parametrización prediga mejor. Un buen Brier histórico de un alfa atenuado tampoco valida el método prospectivamente: esos años ya fueron vistos, las dos cohortes comparten países y choques, y no se justifica un test IID por país.

**Condiciones de integridad:** se verifica el SHA exacto del archivo original GEO, de la sombra LOG1P y de las 15 alertas. Las ediciones UCDP 23.1, 24.1, 25.1 y 26.1 se comprueban por SHA-256 antes de calcular el Brier; no hay imputación de etiquetas ausentes como ausencia de violencia. El archivo prospectivo emitido no se modifica. Ningún resultado oficial de 2027 se conoce en este momento.

**Ficheros de reproducción:** \`scripts/experiment_geo2027_log1p_inactive_attenuation_frontier.py\`, \`scripts/test_experiment_geo2027_log1p_inactive_attenuation_frontier.py\`, y \`data/geo2027-log1p-inactive-attenuation-frontier.json\`. GitHub Actions reconstruye el informe completo y compara bytes antes de permitir su publicación.

