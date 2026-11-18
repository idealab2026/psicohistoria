# GEO H2 — Robustez del ranking a revisiones de resultados UCDP

**Prueba histórica predefinida (18 noviembre 2026).** Esta auditoría utiliza exclusivamente dos resultados ya reproducidos y congelados: la serie anual de Brier bajo edición objetivo UCDP 25.1 y las variaciones observadas con el **mismo vector de probabilidades** al sustituir resultados por edición 26.1.

Se comprueba el orden por Brier de los cuatro modelos: Markov binario, Markov cuatro estados, Markov global y prevalencia quinquenal global. El menor Brier gana. Se comparan los órdenes completos, posibles empates y cada pareja de modelos, por año y sobre el total exactamente comparable.

**Cohorte:** 196 GWNO × 11 años objetivo **2014–2024** = 2.156 filas. El informe previo de rolling cubre 2014–2025: **2025 se excluye obligatoriamente** de ambos agregados para no combinar paneles con denominador diferente.

Para cada modelo y año:

```
Brier_26.1_con_p_fija = Brier_25.1_original + delta_Brier_medida_por_revisión
```

Los cambios medidos se comprueban contra la cota absoluta de `k/196` y sus once promedios contra el informe SHA-verificado. El año 2017 concentra la única reclasificación binaria entre las dos ediciones en este universo.

**Advertencia temporal:** las ediciones utilizadas como simulaciones en orígenes antiguos no estaban disponibles entonces. Esta comparación es un diagnóstico retrospectivo, no acredita capacidad predictiva prospectiva, ni constituye una serie de 11 años estadísticamente independiente.

El informe `data/geo-h2-2526-fixed-brier-ranking-stability.json` publicará el ranking anual y global y la distancia absoluta entre los cuatro modelos una vez reproducido y comprobado en CI. El programa no cambia ninguna predicción, SHA, ni alerta GEO2027/GEO2028.
