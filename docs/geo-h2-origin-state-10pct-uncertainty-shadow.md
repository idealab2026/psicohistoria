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
