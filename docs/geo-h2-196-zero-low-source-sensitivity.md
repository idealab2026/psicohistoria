# GEO H2 — Fragilidad del umbral de violencia cero frente a 1–24 muertes

**Diseño retrospectivo, 18 noviembre 2026.** Se extiende el diagnóstico de Ruanda a los **196 países GWNO de evaluación** del modelo H2 de cuatro estados. Mantiene el mismo origen simulado 2021, objetivo 2023 con etiquetas oficiales **UCDP 26.1** y matriz de transición categórica, hiperparámetros y prior de 199 países originales de entrenamiento.

## Fuentes y pregunta

Se reconstruyen los registros oficiales UCDP OrganizedViolenceCY ediciones 23.1 y 24.1, SHA verificados, hasta el año 2021. Los estados del modelo son 0 fallecidos, 1–24, 25–99, ≥100. Se define una revisión **cero ↔ baja intensidad** solamente cuando el recuento cruza entre 0 y 1–24. Se excluyen de este grupo otras revisiones (incluidas las de 0 a ≥25) para no confundir mecanismos.

Las revisiones oficiales de recuento se dividen en dos bloques disjuntos:
- **Z:** todas las revisiones 0 ↔ 1–24.
- **O:** todas las demás revisiones, incluidos cambios de alta intensidad y dentro de estado.

Se reconstruyen cuatro versiones: `00` ninguna revisión, `10` solo Z, `01` solo O, `11` todas las revisiones. El pronóstico se calcula para los mismos 196 países con los mismos 199 países del prior global. Se verifican exactamente las **392 probabilidades** originales y revisadas de la auditoría previa.

La contribución de Z a un resultado `f` se calcula como `[f(10)-f(00)+f(11)-f(01)]/2`. La de O es `[f(01)-f(00)+f(11)-f(10)]/2`. Se aplica tanto a la **probabilidad H2** como al **Brier con etiqueta 26.1 fija**. Sus sumas deben ser exactamente iguales al cambio total.

Se publica por país el estado inicial de ambas ediciones, las cuatro probabilidades, el efecto de cada grupo, el Brier de los cuatro escenarios y las revisiones propias. Se distinguen efectos directos del registro del país y efectos transmitidos por la matriz global.

## Limitación científica

Es sensibilidad retrospectiva al historial de origen, no un experimento causal ni un test prospectivo con emisiones realmente fechadas. Las ediciones oficiales 23.1 y 24.1 son posteriores a algunos orígenes simulados. Los 196 países están correlacionados y los cambios del prior global comparten información entre países.

La fuente de destino UCDP 26.1 es idéntica en los cuatro escenarios, evitando mezclar revisión de etiquetas con revisión del entrenamiento. No se modifica ninguna alerta o predicción registrada GEO2027 ni GEO2028.

Los resultados numéricos se incorporan al archivo `data/geo-h2-196-zero-low-origin-vintage-sensitivity.json` una vez reproducida y auditada la primera ejecución de GitHub Actions.

## Resultados reproducidos

El replay SHA-verificado detecta **93** revisiones de recuentos anteriores o iguales a 2021 en los 199 países del universo de entrenamiento y **5** cruces de 0 a 1–24 fallecidos. Estos cinco cruces afectan directamente a solo tres GWNO:

| GWNO | País | Años revisados y recuentos |
|---|---|---|
| 516 | Burundi | 1993: 0→6; 2011: 0→2 |
| 517 | Ruanda | 2021: 0→7 |
| 678 | Yemen (Yemen del Norte) | 2000: 0→19; 2002: 0→2 |

Se recuperan exactamente las **392 probabilidades de extremos** previamente publicadas (196 con fuente 23.1; 196 con fuente 24.1).

| Resultado de Shapley del bloque cero↔baja intensidad | Magnitud |
|---|---:|
| Mayor cambio absoluto de probabilidad por país | 0,1124370 (11,2437 pp; Ruanda) |
| Cambio medio de probabilidad sobre 196 países | +0,0004997690 |
| Cambio medio de Brier con etiqueta 2023 26.1 fija | +0,0002183904 |
| Países con cambio distinto de cero (>10⁻¹⁰) | 196 |

Los otros cambios de origen distintos de cruces cero↔baja intensidad aportan, en el agregado, **+0,0003109744** de probabilidad media y **+0,0000258357** de Brier medio.

Entre los tres países cuyo historial cruza directamente el umbral, la contribución de Ruanda supera ampliamente las de Burundi y Yemen. La mayoría del resto de los países presenta efectos indirectos pequeños que se transmiten por el prior global. La comparación no implica que las 196 probabilidades tengan errores de magnitud relevante.

**Advertencia:** un Brier mayor en el agregado histórico 2023 significa peor ajuste para el mismo conjunto de etiquetas, no necesariamente peor desempeño futuro. No se puede extrapolar automáticamente la clasificación de fuente ni la magnitud de 2023 a todas las revisiones históricas.

[Informe íntegro de los cuatro escenarios para 196 países](../data/geo-h2-196-zero-low-origin-vintage-sensitivity.json) · [Reproductor SHA](../scripts/experiment_geo_h2_196_zero_low_vintage_sensitivity.py) · [Pruebas](../scripts/test_experiment_geo_h2_196_zero_low_vintage_sensitivity.py).
