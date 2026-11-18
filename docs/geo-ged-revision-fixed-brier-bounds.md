# GEO — Cuánto puede cambiar Brier únicamente por revisiones de UCDP

**18/11/2026.** Auditoría matemática retrospectiva, no una reemisión GEO2027/GEO2028 ni una evaluación de skill histórico prospectivo.

## Planteamiento con probabilidades fijas

Sea `p_i` una probabilidad binaria fija, `y_i∈{0,1}` la etiqueta histórica original y `y'_i` la etiqueta revisada. La diferencia exacta del error cuadrático por fila es

```
(p_i-y'_i)^2 - (p_i-y_i)^2 = (y'_i-y_i)(1-2p_i)
```

Si en un mismo universo de `N` observaciones se revisan `k` etiquetas binarias, independientemente de dónde estén sus probabilidades:

- Cambio absoluto del **Brier de un modelo fijo**: a lo sumo `k/N`.
- Cambio absoluto de la **diferencia entre los Brier de dos modelos fijos**: a lo sumo `2k/N` (y como ambas puntuaciones están en [0,1], también se puede limitar a 1).
- Si un modelo tiene menor Brier que otro por margen **superior** a `2k/N`, ninguna de esas modificaciones de etiquetas puede invertir su clasificación; para márgenes inferiores o iguales no queda demostrada ninguna inversión.
- Se conserva el denominador. El resultado **no** cubre una edición que incorpore/elimine países o años sin mantener un universo comparable.

Para un indicador binario de transición (por ejemplo, salida 10), puede emplearse el número de etiquetas de transición **de cuatro estados** afectadas como `k`: es una cota posiblemente holgada porque no todo cambio de estado de cuatro categorías cambia el indicador de salida particular.

## Resultados con seis comparaciones oficiales históricas

El input SHA-verificado procede de las auditorías ya publicadas de ediciones GED, y del conteo exacto de transiciones afectadas de la PR #115. La tabla presenta el **máximo algebraico absoluto de cambio en Brier de un solo vector fijo**, en puntos porcentuales de la escala de Brier (no porcentajes de error ni tasas de acierto):

| Ediciones | Años y países comparables | Revisiones binarias anuales | Máximo Brier anual | Transiciones de cuatro estados revisadas | Máximo Brier de un evento de transición |
|---|---:|---:|---:|---:|---:|
| 19.1→20.1 | 1560 | 2 | 0,1282 pp | 4/1365 | 0,2930 pp |
| 20.1→21.1 | 1764 | 1 | 0,0567 pp | 2/1568 | 0,1276 pp |
| 21.1→22.1 | 1960 | 6 | 0,3061 pp | 10/1764 | 0,5669 pp |
| 22.1→23.1 | 2156 | 0 | 0 pp | 0/1960 | 0 pp |
| 20.1→23.1 | 1764 | 7 | 0,3968 pp | 12/1568 | 0,7653 pp |
| 21.1→23.1 | 1960 | 6 | 0,3061 pp | 10/1764 | 0,5669 pp |

Para diferencias entre **dos** modelos fijos, duplicar cada cota (salvo el límite absoluto de 1 en la escala de Brier). Ejemplo: entre GED21.1 y GED22.1, el máximo cambio por medición de la comparación de Brier de un evento de transición es `20/1764 = 0,01134`, o **1,1338 puntos en una escala de Brier ×100**.

**Interpretación de unidades:** `Brier=0,01` frente a `Brier=0,02` difieren en 0,01 unidades; llamarlo «un punto porcentual de Brier» solo es una forma de mostrar la escala multiplicada por 100, no un cambio en probabilidad predicha.

### Lo que NO demuestra

Estos números **no son diferencias de Brier observadas entre ediciones**. En ausencia del vector histórico con probabilidades fijas por país y año, solo delimitan matemáticamente la magnitud máxima que pueden introducir revisiones de etiquetas en un universo constante. No se estima qué modelos fueron mejores ni se comparan supuestos pronósticos retrospectivos con originales emitidos en su día.

Las seis comparaciones se solapan; no son seis muestras independientes y no se deben sumar. La ausencia de un cambio de clasificación `best≥25` no garantiza ausencia de variaciones en recuentos, intensidades, features ni probabilidades de un modelo **reentrenado**. La cota se aplica exclusivamente a mantener `p` constante al evaluar dos etiquetados.

**Cobertura:** GED19.1 no incluía Siria; se excluye en 19.1→20.1. Los ceros de eventos registrados no deben interpretarse como ausencia de violencia real. Los ZIP oficiales y su cobertura están auditados en los informes anteriores; este paso no descargó ni certificó de nuevo esos ZIP.

## Artefactos

- [Informe derivado por edición](../data/geo-ged-revision-fixed-brier-bounds.json)
- [Implementación determinista](../scripts/audit_geo_ged_revision_fixed_brier_bounds.py)
- [Pruebas sintéticas de cotas y controles de procedencia](../scripts/test_audit_geo_ged_revision_fixed_brier_bounds.py)

## Próxima prueba falsable

Obtener un **vector histórico fijo, identificado y reproducible** de pronósticos por país, origen, horizonte y cohorte común; calcular el término exacto `(y'_i-y_i)(1-2p_i)/N` para cada cambio de etiqueta, y determinar si el signo real de la diferencia entre modelos cambia. Sin vectores fechados **antes** de los resultados, calificar el cálculo como reanálisis retrospectivo, nunca validación prospectiva.

Los hashes SHA y probabilidades originales GEO2027/GEO2028 se mantienen intactos.
