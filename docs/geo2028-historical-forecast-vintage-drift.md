# GEO2028 — Sensibilidad histórica de probabilidades a revisiones UCDP

**Estudio retrospectivo de ediciones 23.1–26.1; protocolo de la PR #83, 15/11/2026.** Esta investigación cuantifica cuánto cambiarían las probabilidades GEO si una edición oficial anual revisara etiquetas históricas **sin mover la fecha de origen de la predicción**.

## Hipótesis y problema

La investigación anterior, reproducida desde los originales UCDP, detectó los siguientes cambios de umbral binario estatal ≥25 muertes entre archivos de ediciones consecutivas:

| Primera edición → revisada | Países-año comunes | Etiquetas binarias reclasificadas |
|---|---:|---:|
| 23.1 → 24.1 | 6544 | **2** |
| 24.1 → 25.1 | 6740 | **4** |
| 25.1 → 26.1 | 6936 | **3** |

Esos recuentos no cuantifican directamente cambios de probabilidad. **Una única corrección histórica puede modificar parámetros de transición globales y probabilidades de decenas o cientos de países**, aunque sus propias etiquetas y estados de origen permanezcan intactos.

El nuevo estudio mide esa sensibilidad utilizando exactamente el algoritmo original publicado para GEO2027/GEO2028: Markov binario por país, transición global con Laplace(1), regularización nacional hacia el valor global con fuerza 20, referencia global Laplace para los cinco años previos, horizontes 2 y 3. **No se vuelve a optimizar el modelo ni se elige un algoritmo después de mirar los resultados.**

## Diseño histórico sin fuga temporal

Se descargan y autentican los mismos cuatro archivos anuales oficiales ya bloqueados por SHA-256 en scripts/backtest_archived_country_vintages.py: versiones 23.1 (hasta 2022), 24.1 (hasta 2023), 25.1 (hasta 2024) y 26.1 (hasta 2025). Cada comparación mantiene **el mismo origen, los mismos 196 países y el mismo horizonte**, y reconstruye el modelo con las observaciones **≤ año de origen**, aunque la edición posterior contenga años más recientes.

| Origen inmutable | Edición original | Reediciones utilizadas | Horizontes probados |
|---|---|---|---|
| 2022 | 23.1 | 24.1, 25.1, 26.1 | 2 y 3 años |
| 2023 | 24.1 | 25.1, 26.1 | 2 y 3 años |
| 2024 | 25.1 | 26.1 | 2 y 3 años |

Son **seis parejas solapadas** y doce comparaciones horizonte-pareja: no doce experimentos independientes, ni réplicas de habilidad prospectiva. No se utilizan resultados de los años objetivo. Las predicciones antiguas son **reconstrucciones ex post**, no pronósticos emitidos entonces.

El programa scripts/diagnose_geo2028_historical_forecast_vintage_drift.py comprueba primero que la misma fuente oficial 26.1 reconstruye con precisión decimal **todas las 196 probabilidades originales de GEO2027 a H2 y de GEO2028 a H3**, sin alterar esos archivos. Si falla esa reproducción, se detiene el estudio histórico.

## Atribución algebraica dentro de cada vintage

Para cada país y horizonte, la comparación requiere tres valores:

- **A:** modelo original ajustado con la edición inicial y estado de origen inicial.
- **B:** modelo reajustado con la edición posterior, truncada al **mismo año de origen**, pero manteniendo el **estado inicial antiguo**.
- **C:** el mismo modelo revisado de B, ahora usando el estado del origen según la edición revisada.

Por tanto, exactamente:

\[
p_C-p_A=(p_B-p_A)+(p_C-p_B).
\]

La primera componente representa un **cambio del kernel** motivado por revisiones históricas y/o composición de la fuente; la segunda aísla la **reclasificación del estado de origen**. El desglose es secuencial, depende del orden y **no identifica causas geopolíticas**.

El análisis calcula, separadamente por horizonte, la media, la mediana, el percentil 95 empírico y el máximo de cambios absolutos de probabilidad; el número de países que cambian **al menos 1, 5 o 10 puntos porcentuales**; reclasificaciones de una decisión basada en 50 %; composición del top 20 (desempate por ID GWNO declarado), diez mayores variaciones individuales, recuento de cambios de estado de origen y diferencias de la referencia global.

La precisión de los percentiles es **descriptiva de los 196 países observados**, no un intervalo de confianza. Los rankings con probabilidades empatadas son sensibles al desempate por ID GWNO y no tienen interpretación de diferencias reales de riesgo entre países.

## Límites y decisión predefinida

Esta prueba mide un tipo de fragilidad de la predicción **ante revisiones del dataset**, no el error predictivo futuro ni la independencia entre países. Las comparaciones solapadas no permiten calcular intervalos IID fiables. Que las ediciones antiguas alteren poco las probabilidades tampoco demuestra que la futura UCDP 27.1 vaya a ser estable.

El informe numérico oficial, derivado por CI de los archivos originales, se guardará en **data/geo2028-historical-forecast-vintage-drift.json** y su igualdad byte a byte será una condición obligatoria de despliegue. Su código y pruebas sintéticas quedan sujetos al allowlist institucional. No se modifican las 620 preguntas emitidas, las primeras versiones públicas ni los criterios de resolución.

**Aplicación futura:** cuando UCDP publique la edición anual 27.1, el protocolo GEO2028 de origen 2026 ya incluye controles de revisiones de 2025. Este estudio histórico permitirá contextualizar la magnitud de esas revisiones, pero el desglose 2025→2026 preregistrado seguirá separando tres componentes (vintage, sorpresa del estado 2026 y refit): **no se atribuirá toda variación a noticias de 2026**.
