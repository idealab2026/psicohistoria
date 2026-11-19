# PSICOHISTORIA · Auditoría de pares GED25.1: fuentes y umbral de 25

**Diseño del 19/11/2026, posterior al muestreo de la PR #135 y anterior al examen de las nuevas variables de fuente/díada.** Se mantiene intacta la edición oficial UCDP GED25.1 y sus 24 anclas preseleccionadas.

## Problema

El estudio [#135](geo-ged251-2021-22-stratified-linkage.md) encontró **14 anclas con al menos un registro UCDP cercano** en el mismo GWNO/año, dentro de 25 km y con intervalo temporal de separación no superior a 3 días. Representan **81 relaciones ancla-vecino**, no necesariamente 81 parejas únicas, y ninguna puede declararse duplicado por proximidad.

Esta fase pregunta qué parte de esas coincidencias exige una revisión de fuentes/actores y qué sensibilidad teórica tendría la etiqueta anual de violencia estatal de al menos 25 muertes ante la supresión hipotética de un evento.

## Datos y protocolo fijados

- Archivo **UCDP GED25.1** [ZIP oficial](https://ucdp.uu.se/downloads/ged/ged251-csv.zip) con SHA-256 e256f1fb20a579d8b2f910e5bae212f486d3002adaa2e4359ace740c737da05d, mismo que #135. Sus columnas dyad_new_id, source_article, best y type_of_violence permiten inspeccionar pistas **internas de UCDP**, no verificar hechos independientemente.
- Recomputar exactamente el JSON previo de 24 anclas, exigir coincidencia y fijar las 14 con vecindad. En cada país-año, reconstruir parejas *no ordenadas* de eventos de tipo 1, distancia ≤25km y separación de intervalos ≤3 días. Una pareja examinada desde ambos extremos cuenta **una sola vez**.
- Para cada par: registrar identidades GED, distancia, separación, precisión espacial de ambos, muertes best, si tienen **el mismo ID de díada** (true, false o null cuando falte), y si comparten **fragmentos de referencia bibliográfica idénticos** de source_article después de normalizar espacios/caja. No se reproducen artículos, títulos ni testimonios; solo solapamientos de hashes calculados en memoria.
- Agregar **todas** las muertes best de eventos tipo 1 de la edición GED25.1 por GWNO/año para las unidades afectadas (también registros sin coordenadas elegibles, si los hubiera). El indicador derivado se define como SUM(best) >= 25; no se debe confundir con un recuento comprobado independiente.
- Prueba exclusivamente **contrafactual de una eliminación**: para cada pareja A/B, calcular por separado si eliminar únicamente A, o únicamente B, cambiaría el indicador anual. Registrar cualquiera/ambas posibilidades. No borrar filas, no sumar supresiones encadenadas y **no afirmar** que A o B sean registros erróneos.
- No utilizar probabilidades GEO ni recalibrar el modelo. Reproducir la cadena documental Burundi y el hash original GEO2027. Ninguna de estas condiciones prueba errores efectivos en UCDP ni cambios reales del Brier.

### Interpretación rigurosa

Una referencia periodística idéntica en dos eventos puede explicar **dependencia editorial**, no necesariamente identidad de víctimas. La misma díada no demuestra el mismo episodio: un mismo par de actores combate múltiples veces. Distintas díadas tampoco garantizan víctimas disjuntas. Coordenadas imprecisas pueden ser centroides compartidos.

Si un solo registro de un par hipotéticamente eliminado no cruza el umbral de 25, ese **test unitario** no cambia la etiqueta; ello no impide que un conjunto de múltiples revisiones demostradas pudiera cambiarla. Si cruza, es un **caso prioritario para una auditoría externa**, no justificación para corregir etiquetas.

### Reproducibilidad

- Pruebas: python3 -B -m unittest discover -s scripts -p 'test_audit_geo_ged251_candidate_source_threshold.py' -v
- Auditoría SHA y JSON: python3 -B scripts/audit_geo_ged251_candidate_source_threshold.py --check-report
- Control público: python3 -B scripts/audit_public.py

La primera ejecución se realizará con el código y preguntas registrados antes de extraer las columnas de citas/díadas. Tras verificar el ZIP oficial, el informe JSON se fijará por commit y CI pasará a exigir repetición exacta. No se certifica independencia periodística ni se estima tasa de duplicación a partir de una muestra estratificada **no representativa**.

**Fuente metodológica:** [UCDP GED 25.1, descarga y codebook](https://ucdp.uu.se/downloads/olddw.html), [metodología oficial UCDP](https://www.uu.se/en/department/peace-and-conflict-research/research/ucdp/ucdp-methodology.html).
