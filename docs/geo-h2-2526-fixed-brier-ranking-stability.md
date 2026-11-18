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

## Resultados reproducidos

- **0/11** años invierten el orden de modelos; **0 inversiones por pares**. La cohorte se mantiene fija en **2.156** país-años.
- Markov cuatro estados termina con menor Brier agregado antes y después de la revisión: `0,044673894 → 0,044307425`. El Markov binario pasa de `0,047473152 → 0,047145623`.
- Diferencia binario menos cuatro estados: `0.002799258575 → 0.002838197967` de Brier; la ventaja de cuatro estados crece `0.000038939393`.
- Cuatro estados gana **8/11** años y el Markov binario **3/11** (2016, 2020, 2024) en ambas ediciones.
- La única etiqueta revisada aparece en **2017**, GWNO **100**. El ranking de los cuatro modelos tampoco cambia en ese año.
- El informe anterior de rolling incluye también 2025. **No** se utiliza su Brier pooled de 12 años: se vuelve a calcular desde los 11 folds pertinentes. Este control evita una comparación estadísticamente incorrecta de 2.156 contra 2.352 casos.

[Informe JSON de rankings anual y agregado](../data/geo-h2-2526-fixed-brier-ranking-stability.json) · [Código de recálculo](../scripts/audit_geo_h2_2526_fixed_brier_ranking.py) · [Pruebas](../scripts/test_audit_geo_h2_2526_fixed_brier_ranking.py)

La ausencia de inversión del ranking es una conclusión **limitada a esta revisión UCDP 25.1→26.1**, con estos modelos y país-años. No se extrapola a todas las revisiones, cambios de entrenamiento ni a validación predictiva prospectiva.
