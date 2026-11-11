# GEO-2027 — Incertidumbre conjunta de las 15 alertas prospectivas

**11 de noviembre de 2026 · Sensibilidad antes de observar ningún resultado 2027.**

## Problema

La cohorte `PSICO-GEO2027-TRANSITION-ALERTS-V1` tiene **10 alertas de entrada** entre países inactivos en 2025 y **5 alertas de resolución** de umbral entre países activos en 2025. Las probabilidades proceden de la emisión original GEO-2027 de noviembre de 2026.

El modelo estima probabilidades marginales por país, pero no proporciona una distribución conjunta entre países. La suma de riesgos individuales siempre identifica el **número esperado** de cambios, independientemente de la dependencia. En cambio, no permite determinar de forma única la probabilidad de **ningún cambio**, la varianza del número de cambios o un intervalo predictivo conjunto.

El nuevo script `scripts/diagnose_geo2027_alert_count_dependence.py` lee el documento de las 15 alertas exactamente publicado, coteja el SHA-256, el primer commit público, el código generador original, el manifiesto y la auditoría. Si cambian, **no produce resultados**.

## Escenarios algebraicos, no modelos calibrados

El objetivo 2027 se mantiene como indicador binario de cambio respecto al estado conocido en 2025, sobre la base UCDP de **al menos 25 muertes anuales por violencia organizada estatal**. No es ni el comienzo de un nuevo conflicto ni el fin real de una guerra.

Sean `p_i` las probabilidades congeladas de los 10 o de los 5 cambios.

1. **Independencia completa:** distribución Poisson-binomial exacta mediante convolución de Bernoulli; `P(K=0)=∏(1−p_i)`.
2. **Uniforme común / comonotonía:** los indicadores comparten un mismo uniforme `U` y `Y_i = 1[U<p_i]`. Preserva cada probabilidad marginal, pero impone dependencia positiva extrema; en este escenario `P(K=0)=1−max_i(p_i)`.
3. **Shocks comunes distintos por grupo:** uniformes `U_entrada` y `U_resolución` independientes entre sí, con comonotonía **dentro** de cada grupo de alertas.
4. **Mezclas globales:** peso ilustrativo `w ∈ {0, 0.10, 0.25, 1}` de un régimen con uniforme común para las 15 alertas, frente a `1-w` de independencia total. `w` **no** es un coeficiente de correlación observado ni se ha estimado con datos.
5. **Límites agnósticos Fréchet de no evento:** para cualquier dependencia y mismas marginales,
   
   \[
   \max(0,1-\sum_i p_i)\leq P(K=0)\leq 1-\max_i(p_i).
   \]
   
   Son límites matemáticos generales; **no son un intervalo de probabilidad estimado ni confieren cobertura predictiva**.

El programa proporciona, para cada grupo y la suma de las 15 alertas: esperanza, varianza del recuento, probabilidad de cero, de al menos uno y de al menos tres cambios, rango central 2.5 %–97.5 % bajo **cada escenario**, y la distribución completa de probabilidad por número de cambios. La utilidad de publicar las distribuciones completas es poder comprobar que los resultados son internamente coherentes sin introducir nuevos parámetros ajustados.

## Integridad científica

- SHA-256 del documento prospectivo de las 15 alertas: `309b4f270e1d0d6382b7a90ae64c28d7621f96fbf3177a45aaebbffb0f958acb`.
- Primer commit público: `5938db3c93661ce04ed35902b2bdaa68abfb8daa`.
- Horizonte: **2025 → 2027**; los 196 pronósticos originales y los 15 seleccionados permanecen sin cambios.
- **Cero resultados 2027** incorporados. Ninguna probabilidad de dependencia se declara verdadera ni se transforma en una predicción de éxito.
- Las pruebas sintéticas verifican la conservación de marginales, esperanza, masas totales, modelos de dependencia, rechazo de datos corruptos y protección de la emisión original. CI reproduce el informe desde los documentos oficiales y rechaza divergencias.

La amplitud de la incertidumbre puede impedir comprometerse científicamente con afirmaciones como «sucederán exactamente 2 cambios»: **una esperanza bien definida no determina la distribución del recuento sin hipótesis conjuntas adicionales**. El siguiente progreso real requiere fuentes externas que permitan estimar y validar dependencias regionales sin mirar retrospectivamente el objetivo 2027.
