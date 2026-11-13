# ACD2027 — Transportabilidad del histórico hacia la cohorte realmente emitida

**Fecha del análisis:** 13 de noviembre de 2026. **Carácter:** exploratorio, retrospectivo y descriptivo. Ninguna etiqueta de 2027 observada. No se ha modificado ningún pronóstico emitido.

## 1. Pregunta

El modelo secundario ACD p_lag1_group parecía superar al modelo primario p_global_recent5 en un backtest histórico completo de 137 observaciones país-año. Antes de extrapolar esa ventaja a 2027, preguntamos: **¿representa esa muestra histórica a los 32 países que efectivamente tienen una predicción ACD2027 publicada, porque registraban conflicto intraestatal tipo 3/4 en 2025?**

La definición ACD exige ≥1 conflicto intraestatal tipo 3/4 en el país en t+2, condicionado a que el país estuviera activo en t. No es el indicador GEO2027 de al menos 25 muertes ni el indicador NEWCONF2027 de inicio de nuevos conflictos. No registrar un conflicto ACD **no significa paz**.

## 2. Fuentes y protocolo

Reutilizamos, verificadas por SHA-256, **seis ediciones oficiales UCDP/PRIO ACD** y las cuatro parejas temporales separadas por edición:

| Origen del pronóstico retrospectivo | Año objetivo | Países evaluados |
|---|---|---:|
| 2019 | 2021 | 35 |
| 2020 | 2022 | 36 |
| 2021 | 2023 | 32 |
| 2022 | 2024 | 34 |
| **Total** | **4 años objetivo** | **137** |

Se reconstruyen **116 resultados con conflicto registrado**, de **42 países distintos**. Las probabilidades se obtienen solo de la edición del año origen y su historial admisible, nunca de las etiquetas objetivo. Los pronósticos históricos fueron reconstruidos ex post y no poseen un sello de emisión contemporánea.

El conjunto de riesgo real para 2027 se identifica exclusivamente mediante los **32 códigos GWNO fijados en la primera emisión de ACD2027** (origen 2025). El registro de 424 predicciones país × endpoint y los hashes originales de GEO/NEWCONF/ACD/shadow/alertas se autentican antes de efectuar cualquier cálculo. Se comprueba explícitamente que 2027 tiene 0 resultados resueltos.

### Precaución causal y temporal

La pertenencia a la cohorte de países activos **en 2025** se utiliza para **estratificar resultados de 2021–2024 vistos retrospectivamente**. Esta pertenencia no se conocía en 2019–2022, por lo que hay *condicionamiento posterior* y posible sesgo de selección/supervivencia. No se presenta como backtest temporal «limpio», validación externa ni comparación prospectiva confirmatoria.

## 3. Cobertura histórica del conjunto de riesgo 2027

| Medida | Resultado |
|---|---:|
| Países ACD2027 emitidos | **32** |
| Países ACD2027 con alguna evaluación histórica | **31** |
| Países ACD2027 sin evaluación histórica | **1: Haití (GWNO 41)** |
| Países evaluados históricamente que no están en ACD2027 | **11** |
| Observaciones históricas de países de ACD2027 | **109 de 137** |
| Observaciones históricas de países no pertenecientes a ACD2027 | **28 de 137** |

Número de observaciones históricas de los 32 países emitidos: **0:1 país; 1:2; 2:2; 3:5; 4:22**. Estas apariciones no son réplicas independientes. Los 31 países solapados no cubren la totalidad de escenarios de actividad intraestatal futura.

## 4. Resultados: diferencia Brier emparejada

Definimos Δ Brier = Brier(candidato) − Brier(global_recent5). **Negativo = mejor el candidato; positivo = mejor la referencia global.** Cada fila utiliza las probabilidades históricas reconstruidas, sin cambios.

| Subconjunto histórico | N observaciones | N países | Δ lag1 − global | Δ country-EB − global |
|---|---:|---:|---:|---:|
| Histórico completo | 137 | 42 | **−0,003472** | +0,005387 |
| Países de ACD2027 con soporte histórico | **109** | **31** | **+0,008157** | +0,004316 |
| Países fuera de ACD2027 | **28** | **11** | **−0,048742** | +0,009555 |
| 2021–2022 completo | 71 | 39 | −0,013976 | +0,007006 |
| 2023–2024 completo | 66 | 36 | +0,007827 | +0,003644 |
| 2021–2022, países de ACD2027 | 54 | 28 | +0,001498 | +0,002629 |
| 2023–2024, países de ACD2027 | 55 | 30 | +0,014694 | +0,005972 |

**Observación principal:** la aparente superioridad agregada de lag1 procede de un subconjunto de países que ya no pertenece al conjunto de riesgo emitido para ACD2027. Dentro de los 31 países de la cohorte emitida que sí estuvieron presentes históricamente, el signo se invierte: **gana la referencia global**. El signo de lag1 − global es **positivo** dentro de esta cohorte tanto en el bloque temprano como en el tardío. La ventaja global de lag1 tampoco se sostiene en el bloque reciente de 2023–2024.

No se deben interpretar estos resultados como una estimación no sesgada de rendimiento futuro, porque el conjunto 2025 se eligió usando información posterior a las fechas de las pruebas históricas.

## 5. Ponderación y dependencia entre países

El cálculo principal pondera **cada evaluación país-año**, por lo que un país presente cuatro años aporta cuatro veces y uno presente un año aporta una vez. Se publica también, **solo como diagnóstico**, un cálculo que promedia primero cada país y después hace la media entre países:

| Grupo | Δ lag1 ponderado país-año | Δ lag1 ponderado cada país por igual |
|---|---:|---:|
| Histórico completo | −0,003472 | −0,022461 |
| Países de la cohorte ACD2027 | **+0,008157** | **+0,017388** |
| Países no incluidos en ACD2027 | −0,048742 | −0,134765 |

La ponderación modifica el estimando, **no es una corrección validada** para el sesgo de selección ni una propuesta para cambiar el protocolo futuro de puntuación. Los bloques 2021–2022 y 2023–2024 no comparten filas, pero sí muchos códigos país y shocks geopolíticos correlacionados. No hay p-valores IID, inferencia de independencia, ni afirmación de significación estadística.

## 6. Decisión científica

1. **Conservar el modelo ACD2027 primario p_global_recent5**: sustituirlo por lag1 basándose en el resultado histórico global sería difícil de defender incluso descriptivamente en la cohorte que se pretende evaluar en 2027.
2. Mantener lag1 y country-EB como **comparadores exploratorios ya emitidos**, sin cambiar probabilidades, modelo primario, endpoints ni sellos de primera emisión.
3. Exigir evidencia independiente de futuros años objetivo, y mayor diversidad de ventanas temporales, antes de atribuir superioridad generalizable a un modelo.
4. Interpretar los países no presentes en la historia y sus probabilidades como zona de incertidumbre, no como éxito o fracaso conocido.

## 7. Reproducción y trazabilidad

El script institucional scripts/diagnose_acd2027_historical_transferability.py autentica fuentes históricas y futuras emitidas, reconstruye exactamente las 137 filas y verifica el Brier original publicado. El archivo **data/acd2027-historical-transferability.json** congela el desglose y las diferencias exactas. Las pruebas de scripts/test_diagnose_acd2027_historical_transferability.py comprueban series sintéticas con países recurrentes, 2025 sin soporte histórico, particiones disjuntas, ponderación por país y rechazo de entradas incompatibles.

La acción de integración continua acd2027_historical_transferability reproduce desde cero las seis fuentes oficiales, verifica que el informe congelado coincide byte a byte y bloquea el despliegue ante diferencias. Ni el script ni el informe cambian los pronósticos prospectivos emitidos.
