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

## Interpretación y decisión metodológica

Se dibuja una **frontera de Pareto descriptiva** de cinco puntos sobre (i) Brier agregado histórico 2024–2025 **ya observado** y (ii) anchura media de banda hipotética de ±10 muertes para la emisión 2027, **no una distribución estadística de revisión**. Un alfa es *dominado* si otro es igual o mejor en ambos ejes y estrictamente mejor en al menos uno. Es una herramienta de diagnóstico, **no un algoritmo de selección de un modelo ganador** ni una prueba estadística.

Una mejora de robustez trivial al disminuir \(\alpha\) no demuestra que la nueva parametrización prediga mejor. Un buen Brier histórico de un alfa atenuado tampoco valida el método prospectivamente: esos años ya fueron vistos, las dos cohortes comparten países y choques, y no se justifica un test IID por país.

**Condiciones de integridad:** se verifica el SHA exacto del archivo original GEO, de la sombra LOG1P y de las 15 alertas. Las ediciones UCDP 23.1, 24.1, 25.1 y 26.1 se comprueban por SHA-256 antes de calcular el Brier; no hay imputación de etiquetas ausentes como ausencia de violencia. El archivo prospectivo emitido no se modifica. Ningún resultado oficial de 2027 se conoce en este momento.

**Ficheros de reproducción:** \`scripts/experiment_geo2027_log1p_inactive_attenuation_frontier.py\`, \`scripts/test_experiment_geo2027_log1p_inactive_attenuation_frontier.py\`, y \`data/geo2027-log1p-inactive-attenuation-frontier.json\`. GitHub Actions reconstruye el informe completo y compara bytes antes de permitir su publicación.

