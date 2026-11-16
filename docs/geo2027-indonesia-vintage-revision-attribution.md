# GEO2027 — Atribución de revisiones históricas de Indonesia (UCDP 23.1 → 26.1)

**16/11/2026 · Estudio retrospectivo H2 con origen fijo 2022.** Ninguna predicción histórica se publicó en 2022; la lista real de alertas GEO2027 (origen 2025) permanece inmutable, y no existen etiquetas oficiales de 2027 resueltas.

## Pregunta

La comparación de seis parejas históricas de UCDP encontró que, con origen **2022**, una corrección de las probabilidades históricas intercambiaba **Indonesia** por **Kirguistán** dentro del top-5 de resolución de violencia estatal ≥25 muertes anuales. Con la edición 23.1 Indonesia tenía una probabilidad de seguir activa en 2024 del 65,7575 %, mientras que con la 26.1 pasa al 71,2182 %, cambio de **+5,4606 pp**. Las probabilidades de Kirguistán varían mucho menos.

La nueva pregunta es **qué cantidad de esta variación procede del historial nacional de Indonesia y cuánto de la tasa global de transición estimada con otros países**. Es crucial no contar dos veces las transiciones nacionales: la media global incluye al propio país.

## Método replicable

Se usan los cuatro originales oficiales UCDP OrganizedViolenceCY 23.1/24.1/25.1/26.1, con SHA-256 declarados en `scripts/backtest_archived_country_vintages.py`. Cada fichero posterior se recorta al 2022 de origen **antes de calcular cualquier transición**. Se reconstruyen los conteos de Markov país-año de los estados binarios `sb_total_deaths_best >=25` y la fórmula original de GEO2027: Laplace global 1, shrinkage hacia global 20, dos pasos desde el estado de 2022.

Las cuentas globales se dividen sin solapamientos: `G = L + O`, donde `L` contiene las transiciones de Indonesia y `O` las de todos los demás países. Para cada país objetivo se define

\[
p(L,O) = \operatorname{Markov2}\bigl(s_{2022},\;q^{\mathrm{local}}(L,G=L+O)\bigr).
\]

Se generan cuatro contrafactuales **matemáticos, no ediciones reales de UCDP**: `p00=p(L0,O0)`, `p10=p(L1,O0)`, `p01=p(L0,O1)`, `p11=p(L1,O1)`. La variación se reparte con Shapley de dos factores:

\[
\phi_L=\tfrac12[(p10-p00)+(p11-p01)],\quad
\phi_O=\tfrac12[(p01-p00)+(p11-p10)].
\]

Por construcción, \(\phi_L+\phi_O=p11-p00\), sin residuo. La aportación nacional **incluye su efecto sobre el prior global**; la aportación del resto de países excluye siempre al país analizado. Se informa por separado de la interacción bruta \(p11-p10-p01+p00\), repartida a medias por Shapley.

Se repite la descomposición para Indonesia y Kirguistán en las comparaciones 23.1→24.1, 23.1→25.1 y 23.1→26.1. Los resultados se cotejan contra el estudio independiente de revisiones H2/H3 ya publicado, el listado exacto histórico de alertas y las 196 identidades GWNO congeladas. El análisis lista los años de cambios en etiquetas binarias históricas y los años ausentes; **no** trata valores ausentes como violencia inexistente.

## Resultados numéricos reproducidos desde las fuentes originales

El ejercicio recorre tres revisiones sobre el mismo origen 2022. Las contribuciones se expresan en **puntos porcentuales** sobre la probabilidad de estado binario activo dos años después:

| Comparación UCDP | Cambio total de Indonesia | Historial nacional `φ_L` | Resto del mundo `φ_O` | Cambio total de Kirguistán |
|---|---:|---:|---:|---:|
| 23.1 → 24.1 | +0,002051 | 0,000000 | +0,002051 | +0,001489 |
| 23.1 → 25.1 | +5,366665 | +5,417825 | −0,051160 | +0,094175 |
| 23.1 → 26.1 | **+5,460642** | **+5,418306** | **+0,042336** | +0,256363 |

El término nacional de Indonesia representa **aproximadamente el 99,2 %** de la variación total 23.1→26.1, con el resto aportando unos **0,8 %**. En 23.1→25.1, el componente de los demás países tiene signo contrario y compensa parcialmente la revisión nacional. Esto demuestra por qué no se debe interpretar un simple desplazamiento del prior global como la única causa.

**Cambios originales de las etiquetas UCDP de Indonesia:** 2019 pasa de estado 0 a 1; 2020 pasa de estado 0 a 1. No se han encontrado otros cambios binarios de ese país hasta el origen 2022 en la comparación 23.1→26.1. El recuento de transiciones Indonesia (filas origen 0/1 y columnas destino 0/1) cambia de `[[13,5],[4,11]]` a `[[12,4],[3,14]]`. Las ediciones 23.1 y 24.1 coinciden para la historia binaria indonesia en este intervalo; las reclasificaciones aparecen en 25.1 y persisten en 26.1.

**Kirguistán como control:** no se revisan sus etiquetas binarias hasta 2022 en estas comparaciones; su matriz de transiciones nacionales se mantiene constante. La variación en su puntuación refleja únicamente las modificaciones de la media global procedentes de otros países.

El intercambio histórico de la lista top-5 no se repite dos veces en episodios independientes: aparece al pasar de 23.1 a 25.1 y sigue presente en 26.1. No hay resultados 2027 observados ni tasas prospectivas de acierto calculadas.

## Auditoría directa de las muertes originales (23.1, 24.1, 25.1 y 26.1)

Para confirmar el origen del cambio de etiqueta, se han extraído de forma independiente las **muertes anuales de violencia estatal** (`sb_total_deaths_best`) de los archivos oficiales originales: XLSX para 23.1 y CSV ZIP para 24.1, 25.1 y 26.1. Cada archivo ha pasado su verificación de SHA-256. No se infieren muertes a partir de las probabilidades del modelo.

| Indonesia · muertes state-based | UCDP 23.1 | UCDP 24.1 | UCDP 25.1 | UCDP 26.1 |
|---|---:|---:|---:|---:|
| 2019 | **16** | **16** | **34** | **34** |
| 2020 | **21** | **21** | **31** | **31** |

Ambos años pasan del lado **inferior a 25** al lado **igual o superior a 25** exclusivamente al introducir la edición **25.1**, manteniéndose las nuevas cifras en **26.1**. La revisión respecto a 23.1 es de **+18 muertes (2019)** y **+10 muertes (2020)** en el estimador `best` de UCDP.

Esta información ayuda a explicar el cambio de la matriz Markov nacional `[[13,5],[4,11]] → [[12,4],[3,14]]`. Al sustituir los estados binarios de dos años adyacentes, también se alteran las transiciones anuales que **entran o salen** de esos años: no son dos cambios de un único contador.

El contraste íntegro de los **seis años 2017–2022** para Indonesia y Kirguistán, en las cuatro ediciones, figura en `data/geo2027-indonesia-raw-death-revisions.json`. Se genera con `scripts/audit_geo2027_indonesia_original_fatalities.py --check-report`, que rechaza cifras fraccionarias, fuentes con SHA incorrecto, duplicados, años ausentes e inconsistencias con la atribución binaria publicada. El CI obliga a la reconstrucción byte-a-byte antes del despliegue.

El campo es *muertes de violencia organizada estatal con la estimación best*, **no todas las muertes violentas** ni un inventario explicativo de incidentes concretos. La investigación **no identifica todavía qué episodios o correcciones editoriales específicas** justifican el aumento de 16 a 34 o de 21 a 31. Tampoco demuestra acierto prospectivo.

## Interpretación rigurosa

Esta es una **atribución algebraica dependiente de la ecuación**, no una estimación causal de cómo el conflicto geopolítico de Indonesia afectó a otros países, ni una distribución de error futuro. Los factores son bloques de datos correlacionados y las combinaciones cruzadas `(L1,O0)` y `(L0,O1)` son contrafactuales artificiales; sus aportaciones cambian si se define otra agrupación de factores. No hay evidencia de que estas revisiones se repitan en UCDP 27.1.

El informe completo debe quedar en `data/geo2027-indonesia-vintage-revision-attribution.json`, con pruebas unitarias y reproducción `--check-report` en GitHub Actions, bloqueando la publicación si difiere algún byte respecto al resultado SHA-pinned.

**No se modifica ninguna emisión GEO2027, GEO2028 ni ninguna de las 15 alertas.** La habilidad predictiva prospectiva demostrada continúa en cero.
