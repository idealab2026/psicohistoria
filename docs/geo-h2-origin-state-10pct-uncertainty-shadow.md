# GEO H2 — Modelo experimental con incertidumbre del estado inicial

**Diseño fijado antes del scoring — 18/11/2026.**

## Hipótesis

El estimador Markov de cuatro estados usa una clasificación exacta para el año de origen: 0 fallecidos, 1–24, 25–99 o ≥100. Los estudios de Ruanda, Burundi y Venezuela demostraron que una corrección pequeña del recuento de 0 a 1–24 puede cambiar abruptamente la probabilidad posterior.

Proponemos una variante de **incertidumbre del estado inicial**, sin reentrenar ni modificar la matriz de transición:

- Para estado 0 observado, probabilidad previa 90% de estado 0 y 10% de estado 1.
- Para estado 1 observado, 90% de estado 1 y 10% de estado 0.
- Para estados 2 y 3, distribución degenerada en el estado observado.

La probabilidad experimental a dos años es la mezcla convexa de las probabilidades condicionales del mismo modelo de cuatro estados. El peso **10% es una hipótesis fija de sensibilidad, no una probabilidad de clasificación errónea estimada estadísticamente** ni un parámetro ajustado al target.

## Evaluación por separado de los dos objetivos

**Diagnóstico histórico 2012–2022 (11 pseudo-orígenes).** Se reproducen las probabilidades hard-state originales de UCDP 23.1 y 24.1 hasta el corte temporal correspondiente, con la misma cohorte 196 GWNO, fuente de etiquetas 2023–2024 y anteriores congelada en UCDP 26.1. Se comparan el Brier original y el experimental y el desplazamiento de probabilidades entre ediciones. Se exige igualdad exacta con el modelo original y con las 11 puntuaciones ya verificadas.

**Nueva emisión prospectiva sombra para 2027.** Usando solo la edición UCDP 26.1 hasta 2025, se emiten 196 probabilidades para 2027 de un **nuevo comparador experimental**, que no reemplaza ni modifica ninguna emisión original del proyecto. No existe etiqueta oficial de resultado 2027 al momento de esta preparación, por lo que no se puede atribuir habilidad predictiva.

**Limitación decisiva:** el corte por año no hace que la fuente 23.1 o 24.1 fuera pública en 2012–2022. El diagnóstico histórico no cumple el requisito completo de emisión *as-of* estricta, aunque la ventana de entrenamiento está recortada correctamente. Por tanto, no es una validación prospectiva. La emisión sombra para 2027 sí puede quedar registrada y congelada antes de observar el objetivo; deberá conservar su primera huella SHA, commit y fecha para poder puntuarla posteriormente con un protocolo fijado.

## Controles

Se exige SHA-256 de los archivos UCDP, mismo entrenamiento global de 199 países y cohorte de 196, exactitud a 12 decimales frente al modelo Markov original, cálculo con idéntica matriz 4×4, no introducir información del target y auditoría institucional de privacidad. Ninguna alerta ni probabilidad GEO2027/GEO2028 ya emitida puede cambiar.

El informe completo se fija en `data/geo-h2-origin-state-10pct-uncertainty-shadow.json` después de la ejecución reproducible.

## Resultados reproducidos desde archivos oficiales

El experimento compara **11 pseudo-orígenes 2012–2022** y 196 GWNO por año bajo UCDP23.1 y 24.1, con resultados 26.1 fijos. El scoring de este diagnóstico es retrospectivo; no demuestra rendimiento *as-of* genuino.

| Métrica agrupada (11×196) | Origen 23.1, modelo original | Origen 23.1, mezcla 10% | Origen 24.1, original | Origen 24.1, mezcla 10% |
|---|---:|---:|---:|---:|
| Brier promedio | 0,044307425 | 0,045265383 | 0,044259672 | 0,045205755 |

La mezcla empeora el Brier medio **+0,000957958** para edición 23.1 y **+0,000946083** para 24.1. A cambio, la diferencia absoluta media entre predicciones de ambas ediciones cambia de **0,001125570** (original) a **0,001076202** (mezcla), una disminución relativa aproximada del 4,4%. El ajuste de pesos **no** se ha optimizado con estas etiquetas. Este resultado constituye una compensación empírica, no una mejora inequívoca.

Para origen 2021 y objetivo 2023, la máxima variación de probabilidad entre ediciones desciende de **0,113295973** a **0,091090483** bajo la mezcla, pero el Brier anual del modelo con mezcla sigue siendo peor que el original en ambas ediciones. Por tanto, **no hay justificación para sustituir el modelo emitido**.

## Emisión sombra nueva para 2027

El informe registra **196 probabilidades adicionales** del comparador de estado inicial incierto, con origen 2025 y fuente UCDP 26.1; estas probabilidades son distintas de todas las emisiones GEO2027 originales, que permanecen inmutables. La evaluación de la cohorte 2027 solo podrá realizarse cuando los resultados oficiales del target sean públicos y después de preservar un identificador de primera publicación verificable con Git commit y fecha.

Como controles reproducibles, para GWNO 2 (Estados Unidos), la probabilidad original calculada con el mismo Markov cuatro estados desde origen 2025 es **0,045387672383**, mientras que la mezcla asume **0,069253010653**. Para GWNO 517 (Ruanda), respectivamente **0,239089456600** y **0,231254307683**.

[Informe JSON completo (incluye las 196 probabilidades sombra)](../data/geo-h2-origin-state-10pct-uncertainty-shadow.json) · [Script reproductor](../scripts/experiment_geo_h2_fixed_origin_uncertainty_shadow.py) · [Pruebas](../scripts/test_experiment_geo_h2_fixed_origin_uncertainty_shadow.py).

**Conclusión metodológica:** 10% es un estrés arbitrario declarado; no representa una probabilidad estimada del error de medición. Para mejorar la precisión y robustez de manera simultánea haría falta modelar la incertidumbre de las fuentes y validarla con emisiones verdaderamente fechadas. La comparación retrospectiva no es suficiente.
