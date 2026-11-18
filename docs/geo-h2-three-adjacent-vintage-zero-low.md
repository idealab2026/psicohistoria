# GEO H2 · Sensibilidad del umbral cero entre tres pares consecutivos UCDP

**Investigación retrospectiva · 18/11/2026.** El resultado de Ruanda y Burundi se había estudiado principalmente con UCDP 23.1 frente a 24.1. Esta ampliación comprueba la dependencia del par de fuentes en tres transiciones: **23.1→24.1, 24.1→25.1 y 25.1→26.1**.

Para cada transición se evalúan los mismos **11 pseudo-orígenes de 2012–2022**, con objetivo dos años después (2014–2024), 196 GWNO congelados y las **etiquetas objetivo UCDP 26.1 fijas**. Son 33 combinaciones de origen y par de edición, equivalentes a 6.468 evaluaciones país-año-par. No son observaciones independientes: se repiten los países, los años y parte de las ediciones.

## Contraste predefinido

Se verifica SHA-256 de las cuatro ediciones oficiales de UCDP OrganizedViolenceCY. Se mantiene el modelo de cuatro estados, Dirichlet(1), shrinkage 20 y corte temporal para cada origen, con 199 países de aprendizaje del prior global. Las intervenciones de fuente se separan en dos bloques:

- **Z:** revisiones de recuentos históricos entre cero y 1–24 muertes, en cualquiera de ambas direcciones.
- **O:** todas las demás revisiones de recuentos históricos, incluidas variaciones dentro de una categoría y cambios entre categorías distintas de 0↔1.

Cada origen y par se reconstruye como factorial 2×2 de cuatro probabilidades `00,10,01,11`. Se calcula el Shapley simétrico de cada bloque para las probabilidades y el Brier con etiquetas 26.1. La suma debe recuperar exactamente el cambio total. Se conservan por origen las revisiones de cero a baja intensidad, su efecto sobre el estado inicial, los cinco países más sensibles, el efecto sobre el Brier y el agregado por pareja. El par 23.1→24.1 debe reproducir las 11 comparaciones de Brier ya publicadas.

## Evidencia y limitaciones

La comparación **no demuestra validez prospectiva**: estas ediciones UCDP se publicaron después de muchos de los orígenes reconstruidos y la edición 26.1 aporta a la vez algunas características de una fuente de entrenamiento y las etiquetas de evaluación. Se informa esta dependencia explícitamente. No hay selección de parámetros basada en las etiquetas de resultado, ni modificación de GEO2027/GEO2028.

La primera ejecución validada generará `data/geo-h2-three-adjacent-vintage-zero-low-11-origin.json`, cuyo contenido se fijará y revisará de nuevo en CI antes de fusionar.
