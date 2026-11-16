# GEO2027 · Auditoría prospectiva de divergencia entre modelos ya emitidos

**Estudio de información predictiva, no de resultados observados · 16/11/2026.** Se comparan los **196 países exactos** de las emisiones congeladas original GEO2027, primera sombra LOG1P y nueva sombra global-only matched α0/α1. **Los resultados UCDP de 2027 no están resueltos.** Ninguna tabla de este informe debe presentarse como acierto, nuevo listado de alertas ni selección de un modelo ganador.

## Hallazgo central: pérdida de discriminación territorial entre países sin muertes en el origen

La sombra global-only elimina deliberadamente la historia de transiciones locales de los países para evitar que el pronóstico de uno dependa de su propia historia nacional. Al quitar esta información, aumenta la transferencia de un prior compartido entre países pero se pierde una parte importante de **heterogeneidad geográfica del riesgo**, incluso antes de observar el desenlace.

| Estrato por muertes de 2025 | Países | LOG1P original: rango de p(2027 ≥25 muertes) | Global-only matched α1: rango | Media LOG1P | Media global-only |
|---|---:|---:|---:|---:|---:|
| **0 muertes** | **154** | **1,37–22,62 %** | **3,50–3,59 %** | 2,87 % | 3,56 % |
| **1–24 muertes** | **8** | 2,75–37,52 % | 8,03–18,70 % | 15,74 % | 11,79 % |
| **≥25 muertes** | **34** | 60,58–98,96 % | 62,79–99,19 % | 89,14 % | 87,62 % |

El rango del grupo 0 pasa de **21,26 puntos porcentuales** en LOG1P original a **0,093 puntos porcentuales** en el global-only. Esto ocurre porque el estado binario observado en 2025 y la mortalidad cero son entradas iguales para los 154 países y el prior global-only es casi común; sus diferencias restantes proceden de pequeños efectos de excluir a cada país del prior y del calibrador específico entrenado sin él.

Dos casos extremos de la diferencia entre emisiones ya fijadas:
- **Burundi** (0 muertes en 2025): **22,62 % → 3,50 %**, una reducción de **19,12 puntos porcentuales**.
- **Senegal** (0 muertes): **18,42 % → 3,52 %**, una reducción de **14,90 puntos**.
- En sentido opuesto, entre países subumbrales **Marruecos** (7 muertes) pasa de **2,87 % → 12,15 %**, y **Catar** (6 muertes) de **2,75 % → 11,14 %**.

No hay dato oficial de 2027 que permita establecer si esas reducciones o aumentos son correctos. Una probabilidad distinta no equivale a una probabilidad mejor calibrada.

## Discrepancia por ranking y magnitud del cambio

Se realizan **comparaciones descriptivas de rankings de probabilidades** del mismo outcome 2027. **No** se reconstruyen ni reemiten las 15 alertas prospectivas originales.

| Ranking descriptivo | Países compartidos | Entradas/salidas |
|---|---:|---|
| Top 15 de todos los países | **11/15** | 4 sustituciones |
| Top 10 entre países inactivos en 2025 | **6/10** | 4 sustituciones |
| Top 5 entre países ya activos en 2025 | **2/5** | 3 sustituciones |

En el universo entero, el cambio absoluto de probabilidad promedio es **2,87 puntos porcentuales**, con máximo **19,12 puntos** (Burundi). **27 de 196 países** cambian al menos **5 puntos**, y **9 países** al menos **10 puntos**, entre la sombra LOG1P original y global-only α1.

La emisión original LOG1P espera **35,9840** países ≥25 muertes en 2027, frente a **36,2157** del nuevo global-only α1: el promedio agregado cambia solo **+0,2317 países esperados**, pese a diferencias nacionales considerables. **La similitud en el total puede ocultar un fuerte desacuerdo país por país.**

Los dos brazos global-only α0 y α1 difieren únicamente en los **8 países con 1–24 muertes en 2025**; son idénticos en los 154 con cero muertes y los 34 ya activos.

## Preparación de una evaluación prospectiva exacta sin usar resultados

La comparación principal registrada en la nueva emisión es:

\[
\Delta_\mathrm{Brier}
=\frac1{196}\sum_{i=1}^{196}
\left[(p^{\mathrm{global\text{-}only}\,\alpha1}_i-y_i)^2-
      (p^{\mathrm{LOG1P\,original}}_i-y_i)^2\right]
\]

con \(y_i=1\) si en la primera edición completa de UCDP para 2027 constan **al menos 25 muertes estatales**, y \(y_i=0\) en caso contrario. **Ninguna etiqueta se inventa ni se imputa a partir de una ausencia de registro.**

La identidad siguiente permite una atribución futura por país **sin calcular hoy el resultado**:

\[
\Delta_\mathrm{Brier} =
\frac{1}{196}\sum_i(p^{\mathrm{nuevo}\,2}_i-p^{\mathrm{viejo}\,2}_i)
-\frac{2}{196}\sum_i(p^\mathrm{nuevo}_i-p^\mathrm{viejo}_i)\,y_i.
\]

El primer término es determinista con las emisiones ya congeladas; el segundo solo se resolverá **cuando existan 196 etiquetas oficiales verificadas**. Se publican los dos efectos matemáticos condicionados a \(y_i=0\) y \(y_i=1\) por país, que **no son predicciones adicionales ni resultados reales**. Los extremos calculables al elegir libremente cualquiera de las \(2^{196}\) combinaciones binarias posibles **no son intervalos de incertidumbre ni inferencia estadística**.

Un test independiente con etiquetas **sintéticas** (todo cero, todo uno y una combinación predeterminada) debe verificar que la identidad reconstruye exactamente el evaluador prospectivo de cinco modelos, y que la auditoría de la emisión rechaza cualquier cambio de SHA.

## Riesgo científico y decisión

El compromiso prospectivo para 2027 sigue intacto. No podemos elegir ahora qué modelo será mejor usando las mismas etiquetas históricas con las que se formularon los modelos. Esta auditoría establece algo **más útil que un nuevo backtest retrospectivo**: qué aspecto del riesgo futuro discrepa, qué capacidades se sacrifican al abandonar la historia nacional y cómo una edición oficial de 2027 permitirá medir cuál de las dos hipótesis tiene menor Brier.

La fuerte concentración de probabilidades del modelo global-only en el grupo de cero muertes debe tratarse como **limitación estructural explícita**: podría mejorar calibración si la diferenciación histórica es ruido, o empeorar precisión si esa historia realmente informa la persistencia de violencia estatal. **No es posible decidirlo antes de puntuar la primera edición oficial completa de 2027.**

Los tres SHA originales permanecen intactos y se auditan junto a la nueva emisión congelada del commit institucional **`52ab9ffe7d49e4574b61a9f6a35c57cf7b43082d`**, SHA-256 **`251595a12758e006cf21dabbb9771e10b5961c469a5317d6b2b1c5de227f3697`**. No existe ninguna nueva alerta, ajuste ni emisión.

**Archivos:** `scripts/diagnose_geo2027_issued_disagreement.py`, `scripts/test_diagnose_geo2027_issued_disagreement.py`, `data/geo2027-global-only-issued-disagreement.json`. Auditoría y publicación se condicionan a igualdad byte a byte del reporte construido exclusivamente desde las emisiones ya SHA-fijadas.
