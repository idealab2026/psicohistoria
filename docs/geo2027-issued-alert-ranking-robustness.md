# GEO2027 — Robustez matemática de las 15 alertas emitidas

**Estudio de sensibilidad, 15/11/2026.** Se mantienen **inalteradas** las 196 probabilidades GEO2027 emitidas, sus 15 alertas secundarias y los presupuestos 10 (entrada en estado binario activo) + 5 (salida del estado activo). Se examina únicamente si el listado de alertas sería estable ante cambios **hipotéticos y adversariales** de las probabilidades individuales.

## 1. El problema que no resuelve una media de revisiones UCDP

El análisis precedente sobre cuatro ediciones reales UCDP (23.1–26.1) encontró que, para el Markov de dos pasos y el mismo año de origen, las variaciones absolutas medias por cohorte no sobrepasaron **0,131 puntos porcentuales**, mientras que un país concreto llegó a variar **5,461 pp**. El percentil 95 más alto de las seis comparaciones históricas H2 fue **0,256 pp**.

Son **descriptivos retrospectivos de ediciones distintas**, con fuentes y orígenes parcialmente solapados; ninguna de las cifras es un intervalo de confianza, un techo garantizado de revisiones futuras ni una distribución de error de pronóstico. Un listado de alertas puede cambiar aunque el Brier medio sea estable, porque una diferencia pequeña en el **límite de selección** puede intercambiar dos países.

## 2. Selecciones y márgenes inmutables

El protocolo original GEO2027 elige:

- Entre **162 países inactivos en 2025**, los **10** con mayor p_model de superar el umbral de ≥25 muertes de violencia organizada estatal en 2027 (*entrada binaria*, no necesariamente inicio de una guerra).
- Entre **34 países activos en 2025**, los **5** con mayor **1−p_model** (*resolución binaria del umbral*, no necesariamente paz o fin de la guerra).

No se intercambian países entre categorías, no se reentrena el modelo ni se cambia el presupuesto.

| Grupo | Último seleccionado | Primero excluido | Margen de puntuación | Radio simétrico que empieza a permitir intercambio |
|---|---:|---:|---:|---:|
| Entrada, top-10/162 | 13,06365 % | 12,43913 % | **0,62452 pp** | **0,31226 pp** |
| Resolución, top-5/34 | 31,15967 % | 29,66083 % | **1,49884 pp** | **0,74942 pp** |

Para todo \(\varepsilon\) estrictamente menor a la mitad del margen del límite, **la composición completa** del grupo se mantiene, aunque cada puntuación país se mueva en cualquier dirección hasta \(\varepsilon\). En caso de igualdad exacta se aplica el desempate público: menor identificador GWNO, y se evalúa explícitamente mediante el algoritmo, no con una afirmación de robustez por redondeo.

## 3. Certificados matemáticos exactos por país

Una prueba de estrés permite a cada país modificar su puntuación de transición \(s_i\) dentro del intervalo

\[
[L_i,U_i]=[\max(0,s_i-\varepsilon),\min(1,s_i+\varepsilon)].
\]

Esta **caja rectangular adversarial** permite cualquier combinación conjunta de cambios; las perturbaciones reales NO se suponen independientes, solo se explora un conjunto matemático más amplio. Para un país \(i\), su **peor rango posible** se obtiene situándolo en \(L_i\) y a todos los demás en \(U_j\); su **mejor rango posible**, situándolo en \(U_i\) y a todos los demás en \(L_j\). En igualdad exacta, el ID GWNO menor precede al mayor.

Con presupuesto k:

- **Permanencia garantizada dentro del escenario** si el peor rango de un país emitido es ≤k.
- **Entrada posible dentro del escenario** si el mejor rango de un país no seleccionado es ≤k.
- La lista es **completamente invariable dentro del escenario** si sus k seleccionados tienen permanencia garantizada.
- Se reportan los seleccionados que *podrían salir* y los excluidos que *podrían entrar*; no se confunden múltiples posibilidades individuales con una combinación simultánea obligatoria.

Los certificados son exactos para esta caja matemática, incluyendo probabilidades saturadas cerca de 0/1. Sus resultados se validan mediante **enumeración exhaustiva de todos los vértices binarios** de pequeños conjuntos sintéticos. No son predicciones de qué países experimentarán revisiones ni probabilidades de intercambio.

## 4. Escenarios predefinidos y prudencia interpretativa

Se calculan los escenarios \(\varepsilon=\) **0; 0,2 pp; P95 H2 histórico máximo (0,256 pp); 0,5 pp; 1 pp; 2,5 pp; máximo H2 histórico observado en un país (5,461 pp); 10 pp**.

Las dos magnitudes derivadas del estudio de revisiones se usan solo como **intensidades ilustrativas**. Aplicar la mayor variación individual histórica a **todos los países a la vez** es una prueba adversarial muy conservadora, no un escenario empíricamente calibrado. En el caso P95, del hecho de que un radio menor que el margen garantice la selección **no se sigue** que haya un 95 % de probabilidad de estabilidad en el futuro.

El reporte público solo interpreta márgenes, estabilidad en la caja, miembros garantizados y miembros potenciales; mantiene 0 etiquetas oficiales observadas para 2027 y no genera porcentajes de acierto.

## 5. Procedencia, reproducibilidad y privacidad

El generador scripts/diagnose_geo2027_alert_ranking_robustness.py verifica contra los SHA originales:

1. La **primera emisión** GEO2027 completa, su manifiesto y los 196 GWNO originales.
2. El documento inmutable de **15 alertas**, SHA **309b4f270e1d0d6382b7a90ae64c28d7621f96fbf3177a45aaebbffb0f958acb**, y el generador original mediante su auditoría de primera emisión.
3. El informe científico del estudio de cuatro ediciones históricas, con SHA de UCDP originales y seis comparaciones H2; dicho informe tiene su propia reconstrucción byte a byte obligatoria en CI.
4. La clasificación de 2025 (**162 inactivos, 34 activos**), los presupuestos y los márgenes exactos; un cambio silencioso de las listas originales bloquea la ejecución.

El informe data/geo2027-issued-alert-perturbation-robustness.json se genera desde fuentes institucionales, se incorpora a GitHub y pasa a requerir reconstrucción **exacta en CI** antes del despliegue. Los datos científicos y pruebas permanecen en el repositorio institucional y no se enlazan a proyectos personales.

**Límites científicos:** este estudio mide la estabilidad de una **decisión basada en probabilidades emitidas** ante perturbaciones matemáticas hipotéticas. No estima su validez predictiva, su bondad de calibración en 2027, su utilidad económica ni su robustez frente a cambios reales de estado de origen causados por revisiones UCDP. Las 15 alertas originales siguen siendo las únicas emitidas y **no se sustituye ninguna por alertas calculadas en escenarios**.

## 6. Resultados de la cohorte real de alertas emitidas

Las seis pruebas sobre los certificados de pertenencia han pasado en GitHub Actions. El informe íntegro, construido con los **15 países y las 196 probabilidades inmutables**, es data/geo2027-issued-alert-perturbation-robustness.json. Los siguientes números representan **permanencia garantizada dentro de cada caja de perturbaciones**, no aciertos en resultados futuros:

| Radio adversarial simétrico por país | Alertas entrada garantizadas (de 10) | Alertas resolución garantizadas (de 5) | Exclusiones que podrían entrar |
|---|---:|---:|---|
| 0 pp | 10 | 5 | 0 y 0 |
| 0,2 pp | 10 | 5 | 0 y 0 |
| 0,25636 pp (P95 H2 histórico más alto de las seis comparaciones) | **10** | **5** | 0 y 0 |
| 0,5 pp | **7** | **5** | 4 y 0 |
| 1 pp | **7** | **3** | 5 y 1 |
| 2,5 pp | **5** | **1** | 15 y 4 |
| 5,46064 pp (máximo individual H2 histórico) | **2** | **1** | 45 y 13 |
| 10 pp | 0 | 0 | 152 y 23 |

En el radio de **0,5 pp** pueden perder su plaza tres de las diez alertas de entrada (las de menor margen al límite), pero ninguna de las cinco alertas de resolución. Con radio de **1 pp**, siete entradas y tres resoluciones mantienen garantizada su inclusión. Los outsiders «podrían entrar» son **posibilidades individuales**; no se afirma que puedan hacerlo todos simultáneamente en una lista que sigue teniendo capacidad 10 o 5.

Con radio **5,46064 pp**, que aplica a cada país una variación tan grande como la **mayor corrección individual jamás observada en las seis comparaciones oficiales H2** —una ampliación adversarial extrema, no una predicción de UCDP—, quedan garantizadas solo:

- **Entrada:** Burundi (GWNO 516) y Senegal (GWNO 433).
- **Resolución:** Haití (GWNO 41).

Las restantes alertas originales pueden seguir siendo seleccionadas; únicamente dejan de tener **permanencia garantizada en esa caja**. La ausencia de garantía no implica error, fallo de predicción ni alta probabilidad de exclusión.

### Consecuencia práctica

Se deben comunicar las alertas GEO2027 con tres capas separadas: **probabilidad original emitida**, **posición y presupuesto congelados**, y **sensibilidad matemática de pertenencia bajo perturbaciones explícitas**. Esta tercera capa es información sobre robustez de una decisión de ranking, no una revisión de la predicción ni un porcentaje de acierto.

El hallazgo explica por qué **estabilidad de la media de las probabilidades** (cambios retrospectivos medios pequeños) **no equivale a estabilidad de cada ranking operativo**, especialmente cerca de sus límites. La primera fuente real de resultados 2027 todavía no existe en el protocolo, así que **el estado prospectivo sigue sin resultados certificados**.
