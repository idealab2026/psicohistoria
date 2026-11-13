# ACD2027 — Frontera exacta de Brier y país pivote (sin observar 2027)

**13 de noviembre de 2026.** Estudio derivado, motivado retrospectivamente, elaborado antes de los resultados de 2027. No constituye una emisión adicional ni modifica el pronóstico ACD2027 publicado el 12-11-2026 a las 22:24:56 UTC. El modelo principal sigue siendo **p_global_recent5**; **p_lag1_group** es un comparador secundario exploratorio.

## Pregunta

Entre los **32 países con conflicto intraestatal ACD tipo 3/4 registrado en 2025**, ¿qué configuraciones hipotéticas de presencia de conflicto ACD en 2027 harían que el Brier del modelo principal fuera menor al del alternativo lag1? Se resuelve exactamente, sin observar 2027 y sin suponer independencia entre países.

El script de reproducción primero verifica todos los documentos originales y manifiestos mediante el auditor existente. La primera emisión ACD es SHA-256 **6cf7d0340a4c25062af7a040586fb6a73a98c9e6ab80473527171c0a5a963d9c**, commit **41db7bd154e0140ced15abd8727a7d52d998852c**. No se descargan ni inventan resultados futuros.

## Dos estratos que ya estaban fijados

| Actividad ACD en el origen | Países | Principal p_global_recent5 | Exploratorio p_lag1_group |
|---|---:|---:|---:|
| Con registro ACD tanto en 2024 como en 2025 | 31 | 0,859195402299 | 0,848030607957 |
| Sin registro en 2024, con registro en 2025: **Sudán del Sur**, GWNO 626 | 1 | 0,859195402299 | 0,546119278779 |

El término \((p_i-q_i)^2\) de Sudán del Sur representa **96,2071 %** de la suma de los 32 términos de discrepancia cuadrática. Eso cuantifica *influencia en la diferencia de los pronósticos*, no contribución al error futuro, importancia geopolítica ni causalidad. Ausencia de un conflicto registrado no significa paz.

## Derivación exacta

Para cualquier resultado binario hipotético \(y_i\), la diferencia de Brier **primario menos alternativo** es:

\[
d_i(y_i)=(p_i-y_i)^2-(q_i-y_i)^2=(p_i^2-q_i^2)-2(p_i-q_i)y_i.
\]

Sea \(s\) la presencia hipotética de ACD en Sudán del Sur en 2027, y \(k\) el número hipotético de los otros 31 países SIN registro ACD en 2027. Dado que ambos vectores tienen probabilidades idénticas dentro del grupo de 31, el promedio exacto depende solamente de esos dos números:

\[
\Delta_{\mathrm{Brier}}(s,k)=\frac{d_{\mathrm{SudanSur}}(s)+k\,d_{\mathrm{otros}}(0)+(31-k)\,d_{\mathrm{otros}}(1)}{32}.
\]

| Contribución individual, sin dividir por 32 | Ausencia ACD (y=0) | Presencia ACD (y=1) |
|---|---:|---:|
| Sudán del Sur | +0,439970472678 | −0,186181774362 |
| Cada uno de los otros 31 países | +0,019060827300 | −0,003268761384 |

**Signo negativo** favorece al modelo global primario; **positivo** al lag1 exploratorio.

## Resultados: frontera exhaustiva

| Sudán del Sur 2027 | Ausencias ACD entre los otros 31 | Menor Brier |
|---|---|---|
| Sin registro ACD | k=0…31 | Alternativo lag1 |
| Con registro ACD | k=0…12 | Principal global |
| Con registro ACD | k=13…31 | Alternativo lag1 |

Si Sudán del Sur **carece de registro ACD en 2027**, el caso más favorable al principal (los otros 31 continúan activos) da \(\Delta=+0,010582464680\). Por tanto, no puede ganar el principal **sea cual sea** el estado de los otros 31 países.

Si Sudán del Sur tiene conflicto registrado, con **12** ausencias entre los otros 31 la diferencia es \(\Delta=-0,000611197283\), mientras que con **13** ausencias es \(\Delta=+0,000086602363\). El umbral exacto es 13, sin redondear previamente las probabilidades.

La cota absoluta de todos los resultados binarios hipotéticos es **[−0,008984793040, +0,032214253718]**. Son extremos matemáticos alcanzables, no intervalos de confianza. Se prueban exhaustivamente los **64 estratos (s,k)**, que resumen todas las \(2^{32}\) asignaciones posibles debido a la simetría de los 31 países.

## Lectura científica correcta

Una hipotética victoria de lag1 no demostraría automáticamente mayor capacidad general de predicción; podría estar determinada por un solo país. Una victoria del primario tampoco validaría su superioridad más allá de esta cohorte. El contraste es **secundario y exploratorio**; los originales y los objetivos GEO2027 y NEWCONF2027 permanecen intactos.

**Reproducibilidad:** scripts/diagnose_acd2027_brier_pivot.py, opción --summary. Tests adversariales y algebraicos: scripts/test_diagnose_acd2027_brier_pivot.py, incorporados al job de calidad existente que ejecuta todos los tests Python. El auditor comprueba SHA, los 424 registros derivados, y el mantenimiento de cero resultados observados de 2027.

**Límites:** No se observa ni imputa ningún resultado 2027; falta de registro ACD no equivale a paz; las revisiones de fuentes y las coberturas incompletas solo se puntuarán conforme a sus contratos futuros originales. No se infieren distribuciones conjuntas, independencia entre países, nuevas probabilidades ni habilidad predictiva demostrada.
