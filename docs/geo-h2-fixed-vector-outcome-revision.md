# GEO H2 · Cambio observado del Brier atribuible solo a etiquetas revisadas

**Estudio retrospectivo reproducible, 18/11/2026.** Se compara la definición de violencia estatal `sb_total_deaths_best ≥ 25` de UCDP OrganizedViolenceCY **25.1 frente a 26.1** en los 196 países GWNO congelados, objetivos históricos **2014–2024**.

Para cada origen (objetivo menos dos años), se reconstruye una única pareja de vectores de probabilidades desde la misma edición de entrenamiento, mediante el modelo Markov binario, cuatro estados, global Markov y prevalencia quinquenal ya publicados. Las dos evaluaciones utilizan exactamente esas mismas probabilidades y los mismos 196 países; **solo cambia la etiqueta de la edición objetivo**. La igualdad de las probabilidades se comprueba por país.

Para cada modelo, el cambio medido de Brier es la suma de `(y_nueva−y_antigua)(1−2p)/N`. Se puede medir separadamente el efecto sobre las diferencias Brier entre pares de modelos, sin comparar modelos reentrenados ni mezclar cambio de etiqueta con cambio de pronóstico.

**No es un test prospectivo:** se construyen retrospectivamente probabilidades para años antiguos con ediciones que no existían entonces; el archivo oficial conserva revisiones posteriores incluso en las features anteriores al origen. El modelo original GEO2027, las sombras, alertas y GEO2028 permanecen inalterados.

Los datos reales deben proceder de la descarga y verificación SHA de los archivos UCDP oficiales, nunca de completar países ausentes con cero. El programa comprueba el universo de países, el estado inicial, los parámetros y las etiquetas contra el informe histórico publicado con anterioridad.

**Estado:** el script y las pruebas científicas se encuentran en la PR de investigación. El JSON de resultados no debe publicarse hasta ejecutar la reproducción de las fuentes y verificar los valores.

Informe esperado: `data/geo-h2-fixed-vector-2526-outcome-revision.json` después de completar la ejecución y bloquear su reemisión en CI.
