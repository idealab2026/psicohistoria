# PSICOHISTORIA · Q-GEO-01 NEWCONF2027 — Protocolo prospectivo v1

**Fecha de preparación del código: 11 de noviembre de 2026.** La preparación no equivale a una emisión. Solo el primer commit público que contenga el documento canónico con los **196 vectores de probabilidad** será el inicio de la predicción. El hash de ese documento quedará inmutable en un manifiesto; futuras revisiones se publicarán separadas y jamás sobrescribirán la primera emisión.

## Estimando y temporalidad

- Objetivo `ANY(newconf=1)` durante **2027**, agregado por país de gobierno (GW) desde la fuente **UCDP Intrastate Country Level Multiple Onset**. Es un evento de *conflicto nuevo* y no debe confundirse con el indicador `onset2` del Country Level Onset, ni con 25 muertes de violencia estatal organizada de GEO-2027.
- Unidad de puntuación: **país-año**, una etiqueta binaria por país. La edición Multiple Onset puede contener múltiples episodios por país-año; se aplica OR sin duplicar unidades. La cantidad de episodios se conserva para comprobaciones descriptivas, no para el Brier.
- Horizonte: **dos años desde origen 2025** hasta objetivo 2027. Las etiquetas de `newconf` están disponibles únicamente hasta **2024**; se prohíbe inferir la etiqueta de 2025 a partir de UCDP/PRIO. El estado de **actividad intrastatal en 2025** sí está disponible en la edición original **UCDP/PRIO Armed Conflict Dataset 26.1**.
- Fuentes de entrenamiento: UCDP **Multiple Onset 25.1** (SHA-256 `5fe7411942aa7e6a38d6386faa64f4d7f0703482509f121c4136c0e3223d7f05`) y UCDP/PRIO **25.1** (SHA-256 `b49f7e80510d8a5779a52d872aef5b26456b3f5cbdd3ec32031339488e81813f`). Etiquetas de `newconf` entre 2000 y 2024; los pares actividad-target del horizonte dos años tienen origen no posterior a 2022.
- Fuente del estado del origen: UCDP/PRIO **26.1** (original `https://ucdp.uu.se/downloads/ucdpprio/ucdp-prio-acd-261-csv.zip`, SHA-256 `5f951743222964674a446e32a5a871077b29bd13349588d85fc59953d89c878a`), solo tipos 3 y 4 y GW de gobierno primario no ambiguo. En **2025, 32 países activos** de una cohorte de 196.
- Cohorte: los **196 países** presentes en el último año 2024 del archivo Multiple Onset 25.1. Países con conflictos previos **no** están excluidos del nuevo objetivo `newconf`.

## Predicción y referencias fijadas antes de 2027

Modelo principal: frecuencia país de `ANY(newconf)` hasta 2024 con *empirical-Bayes shrinkage* de fuerza **20** hacia la frecuencia global condicional a actividad intrastatal del año de origen en un **horizonte 2 años**, utilizando pares históricos disponibles hasta 2024. La tasa de grupo se regulariza a la tasa global histórica (Beta(1,1) y prior20). El estado usado para 2027 procede solamente de la actividad observada en **2025**.

Referencia primaria: **prevalencia global de `newconf` 2020–2024**, suavizada por Laplace. Comparadores: país EB sin actividad y tasa de grupo sin país. Se emiten y almacenan las cuatro probabilidades por país antes de 2027. **No se puede elegir ex post otra especificación primaria**.

Métrica primaria: Brier medio modelo menos Brier medio referencia primaria en los países con outcome de 2027 oficialmente resuelto. Secundarias: log-loss, Brier frente a comparadores, calibración por intervalos, cantidad de eventos esperados/observados, y estabilidad ante revisiones. La primera **edición completa** UCDP Multiple Onset que cubra 2027 definirá el resultado principal. Países no encontrados o fuente incompleta se mantienen *unresolved*, jamás etiquetados 0. Las ediciones revisadas se evaluarán separadas.

Los rankings top-k con empates en la frontera **no producen una selección única**: deberá publicarse intervalo de aciertos posibles por desempate, o renunciar a la métrica top-k. Intervalos bootstrap agrupado por país solo como descriptivos; tres únicos positivos en el contraste de 2023/24 y los datos de selección de modelos ya inspeccionados impiden afirmar skill prospectivo.

## Garantías de independencia e integridad

1. **La emisión del pronóstico requiere un commit público con las 196 probabilidades**, el hash SHA-256 del documento y el hash del generador. No basta un texto que diga «registrado» ni un log temporal de simulación.
2. Ninguna parte del training puede leer etiquetas `newconf` de 2025, 2026 o 2027. La fuente de actividad 26.1 se usa **solo para el estado de origen en 2025**; no se utiliza su revisión histórica para ajustar el modelo.
3. El archivo de pronósticos publicado no se modifica después de la primera emisión. Para publicar un modelo mejorado se crea una **cohorte diferente**, con identificador, fechas y objetivos propios.
4. Esta nueva cohorte NO altera ni recalibra la emisión ya existente `PSICO-GEO2027-STATEBASED25-V1` ni su SHA-256 `5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5`.
5. Antes de recibir el outcome de 2027, las únicas conclusiones válidas son que existen probabilidades emitidas y modelos de referencia; **no se ha validado su precisión futura**.

Este documento no certifica por sí solo el instante de publicación, la presencia de un resultado futuro ni ninguna ventaja estadística.
