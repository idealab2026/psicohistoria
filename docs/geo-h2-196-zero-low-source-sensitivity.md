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
