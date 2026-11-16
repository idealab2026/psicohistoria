# GEO2027 — Robustez formal de las 15 alertas frente a perturbaciones de probabilidades

Fecha de análisis: 2026-11-16. Estado: **análisis de sensibilidad de alertas ya emitidas; no validación prospectiva**.

## Fuentes e invariantes

- Probabilidades originales **intactas**: `data/forecast-2027-ucdp261.json`, SHA-256 del contenido **`5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5`**, 196 países.
- Estado de origen 2025: 162 países inicialmente inactivos y 34 activos.
- Dos listas de decisión independientes: **10 mayores probabilidades de activación** entre los 162 inactivos y **5 menores probabilidades de persistencia** entre los 34 activos.
- La segunda lista no predice una probabilidad de salida explícita: ordena por **menor** `p_model` de permanencia en estado activo, equivalente a mayor probabilidad `1-p_model` de estado inactivo en 2027.
- Este análisis solo considera incertidumbre hipotética de probabilidades. No reconsidera las definiciones UCDP, la membresía de la cohorte ni el estado binario de 2025.

## Definición del certificado

Sea `p_i` la probabilidad original y `epsilon` el límite (en unidades de probabilidad, no en pp) tal que **cada país** puede sufrir cualquier cambio independiente `delta_i` dentro de `[-epsilon, epsilon]`. Para una alerta seleccionada en un top-k descendente, sea `b` la mayor probabilidad original de un país **fuera** del top-k. Su membresía está garantizada para toda perturbación si `p_i - b > 2epsilon`. Para el bottom-k ascendente, sea `b` el menor valor excluido: `b - p_i > 2epsilon`. El criterio estricto evita certificar empates en el límite sin un contrato adicional de desempate.

La condición es **necesaria y suficiente** para garantía independiente de desempates en el escenario adversarial por país: si el margen no supera `2epsilon`, existe una perturbación admisible que produce empate o adelanto de al menos un excluido frente a la alerta considerada. Este resultado concierne **a la pertenencia de cada país individual**; no es una garantía de que el conjunto exacto permanezca sin cambios ni una región estadística de confianza.

## Fronteras originales

| Lista | Última seleccionada | p original | Primera excluida | p original | Brecha |
|---|---|---:|---|---:|---:|
| Entradas, top-10 de inactivos | Rwanda | 13,063649 % | Djibouti | 12,439131 % | **0,624518 pp** |
| Salidas, bottom-5 de activos | Mozambique | 68,840331 % | Iran | 70,339172 % | **1,498841 pp** |

La frontera de entradas podría empatar o invertirse con perturbaciones adversariales simétricas de **0,312259 pp por país**; la de salidas, con **0,749421 pp**. Esas cantidades son umbrales geométricos hipotéticos, no errores reales observados.

## Márgenes individuales (respecto al mejor excluido)

| Tipo | País | p_model | Margen (pp) |
|---|---|---:|---:|
| Entrada | Burundi | 29,069088 % | 16,629957 |
| Entrada | Senegal | 24,045139 % | 11,606007 |
| Entrada | Chad | 22,066068 % | 9,626937 |
| Entrada | Tajikistan | 22,038305 % | 9,599173 |
| Entrada | Azerbaijan | 19,954484 % | 7,515353 |
| Entrada | Algeria | 17,226879 % | 4,787747 |
| Entrada | Congo | 14,989484 % | 2,550353 |
| Entrada | Turkey | 13,199941 % | 0,760810 |
| Entrada | Eritrea | 13,145449 % | 0,706318 |
| Entrada | Rwanda | 13,063649 % | 0,624518 |
| Salida | Haiti | 57,343362 % | 12,995810 |
| Salida | Niger | 65,583398 % | 4,755774 |
| Salida | Angola | 68,294840 % | 2,044332 |
| Salida | Lebanon | 68,352956 % | 1,986216 |
| Salida | Mozambique | 68,840331 % | 1,498841 |

## Garantías por escenarios hipotéticos

| Máxima perturbación individual `epsilon` (pp) | Entradas garantizadas / 10 | Salidas garantizadas / 5 | Total / 15 |
|---:|---:|---:|---:|
| 0,157 | 10 | 5 | 15 |
| 0,312 | 10 | 5 | 15 |
| 0,749 | 7 | 5 | 12 |
| 1,000 | 7 | 3 | 10 |
| 5,750 | 2 | 1 | 3 |

Los valores **0,157 pp y 5,75 pp** proceden de estadísticas del estudio de revisiones UCDP de horizonte tres años, pero **ninguna** representa una cota individual demostrada para las 15 alertas GEO2027: 0,157 es un cambio absoluto **medio** máximo entre países en comparaciones históricas, y 5,75 es un **máximo individual observado** en otras configuraciones históricas. Se presentan solo como **magnitudes de pruebas de estrés** y no se infiere frecuencia, probabilidad ni cobertura de las garantías.

## Conclusiones y límites

1. La estabilidad de la etiqueta binaria al 50 % o del top-20 del estudio de revisiones **no implica estabilidad de listas top-10/bottom-5**, que dependen de fronteras distintas.
2. Dentro de un radio adversarial de ±1 pp, 10 de las 15 alertas conservan forzosamente su membresía: siete entradas y tres salidas. Las otras cinco son **no garantizadas**, lo cual no significa que necesariamente vayan a cambiar.
3. Una comparación *point-in-time* de revisiones sobre las mismas 15 alertas requeriría reconstruir sus probabilidades con ediciones históricas alternativas y verificar compatibilidad de estados, horizontes y cortes. Este certificado no hace tal reconstrucción.
4. Ninguna probabilidad prospectiva se ha recalculado, ninguna predicción se ha sustituido y **ningún outcome 2027 está resuelto**. La capacidad predictiva prospectiva sigue sin demostrarse.

**Reproducción:** `python3 scripts/audit_geo2027_alert_robustness.py`. El código valida la huella SHA-256 de la emisión y recalcula las listas, fronteras y garantías desde las 196 probabilidades originales, rechazando cambios en la fuente.
