# GEO2028 · Primera emisión pública prospectiva, horizonte 2025→2028

**Emitida el 15 de noviembre de 2026 a las 18:27:05 UTC**, según los metadatos públicos del primer commit GitHub. El protocolo, generador y tests quedaron incorporados **antes** de emitir estas probabilidades en el commit institucional principal 83c1be9a03f31c38993350b26ff0ff1e678cb0c5 (PR #75). El primer commit que añadió el archivo íntegro de 196 probabilidades fue **5a7c949f6fe9a352ecb27c4e4193f2f3e92b64d0** (PR #76). La fecha GitHub es metadato auditable, **no notarización temporal independiente**.

## Pregunta definida antes de emitir números

Entre los **196 países GWNO** que figuran en UCDP OrganizedViolenceCY edición oficial **26.1** con registros en 2024 y 2025, ¿cuáles tendrán **al menos 25 muertes anuales de violencia organizada estatal** (indicador binario UCDP) durante el año calendario **2028**?

**Origen observado: 2025. Horizonte 3 años.** Esto **no es** la futura cohorte de **2026→2028 a dos años**, que requiere la publicación oficial completa de los datos de 2026. No es NEWCONF (nuevo conflicto intraestatal), no es ACD (persistencia de conflicto tipo 3/4), no es un pronóstico de paz, y no hay resultados observados de 2028.

## Pronósticos y comparadores registrados

El modelo primario es el Markov por país de **tres pasos**, regularizado hacia las transiciones globales con fuerza 20 y Laplace. La fuente es la misma edición 26.1 SHA-verificada que en GEO2027, con **0 datos posteriores a 2025**. Para reproducir las probabilidades de 2028, el generador vuelve a reconstruir las **196 probabilidades GEO2027 originales a dos pasos**, comprueba que ninguna difiere y solo entonces calcula un tercer paso mediante la misma matriz de transición.

| Vector emitido | Suma de probabilidades de estado activo 2028 |
|---|---:|
| Primario país Markov 3 pasos | **33,438734715114** |
| Comparador global Markov 3 pasos | 32,634322892542 |
| Baseline global Laplace 2021–2025 | 34,529531568280 |

La suma equivale a una esperanza **según cada modelo**, no a una predicción determinista de 33 países activos ni a un resultado observado. En el horizonte 2027 a dos pasos, el vector original sumaba 33,625439663908. Los dos pronósticos comparten origen, fuente y muchos parámetros: la cercanía de los totales **no** los convierte en replicaciones independientes.

## Muestra de países con mayor probabilidad estimada

| País | p(estado activo en 2028) | p original GEO2027 |
|---|---:|---:|
| Colombia | 84,72997 % | 89,37695 % |
| Irak | 84,72997 % | 89,37695 % |
| Afganistán | 84,72997 % | 89,37695 % |
| India | 84,72997 % | 89,37695 % |
| Myanmar | 84,72997 % | 89,37695 % |
| Filipinas | 84,72997 % | 89,37695 % |
| Pakistán | 80,89127 % | 85,97643 % |
| Sudán | 80,79701 % | 86,18973 % |
| R. D. Congo | 78,14461 % | 84,06954 % |
| Etiopía | 76,71020 % | 82,74276 % |

**No se ha estimado la precisión de estas cifras con resultados futuros.** El grupo de seis países empatados con 84,73 % tiene exactamente el mismo valor por la compresión que hace el modelo de sus transiciones observadas; la coincidencia no acredita conocimiento causal o individual del mismo riesgo. El modelo es sencillo, de memoria corta, y puede ignorar shocks estructurales o trayectorias históricas largas.

## Expediente de integridad temporal

- Protocolo preregistrado: docs/geo2028-three-year-preregistration.md, PR #75, commit main **83c1be9a03f31c38993350b26ff0ff1e678cb0c5**.
- **Primer commit público del archivo completo:** **5a7c949f6fe9a352ecb27c4e4193f2f3e92b64d0**, creado el **2026-11-15T18:27:05Z** en la rama pública de PR #76. El commit añadió por primera vez el archivo de 196 filas.
- **SHA-256 del archivo de emisión original:** **fd5832c6896548b053202f2f84bd0f7cd4a75df44462fbd4f259b9d8d4c39bde**. Sus bytes se conservan como fuente canónica; posteriores documentos o explicaciones no modifican esos números.
- Fuente de observaciones **UCDP OrganizedViolenceCY 26.1**: SHA-256 **66910888f5653af42776d2debc1d72fe527559e7f7fc82e69b7c8771467f2d34**, último año **2025**.
- Pronóstico original GEO2027, intacto: SHA-256 **5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5**. Las **424 preguntas país × endpoint de 2027** continúan inalteradas y sin resultados.
- El manifiesto data/forecast-2028-geo3-manifest.json declara expresamente que no hay notarización independiente, no hay outcomes 2028, no existe validación de habilidad predictiva, y que GEO2028/GEO2027 no forman dos muestras independientes.
- El auditor institucional scripts/audit_geo2028_first_public_issue.py comprueba que los bytes del archivo son idénticos a los del primer commit público, que el archivo **no existía en su commit padre**, que el protocolo es un ancestro anterior, que GitHub informó de una fecha anterior al comienzo del año objetivo, que la autoría es institucional y que ninguna probabilidad GEO2027 se ha reescrito. Por política de fusión squash, se obtiene el primer commit desde la referencia pública de PR #76, sin fingir que ese SHA sobreviva como ancestro del commit fusionado en main.
- La verificación automática obligatoria de fuente UCDP y sus 196 predicciones está en el job geo2028_three_year_preregister; el auditor de integridad de emisión debe ejecutarse adicionalmente antes de publicar.

## Contrato de evaluación futura

Cuando exista **la primera edición anual completa oficial de UCDP OrganizedViolenceCY que incluya 2028**, registrar fuente, hora, SHA-256 y cobertura. Las ausencias dudosas no se convierten en ceros; no declarar puntuación certificada sin 196 etiquetas de definición equivalente. La métrica principal **ya pre-registrada** será Brier(p_model) − Brier(p_baseline_global_5y), sobre el mismo riesgo completo; Brier frente a Markov global, log-loss y calibración por estado 2025 son secundarios.

**Limitación esencial:** GEO2027 y GEO2028 comparten el mismo origen 2025, indicadores y estructura de modelo, por lo que sus resultados no representan pruebas independientes aunque los años objetivo difieran. Emitir antes de conocer las etiquetas sí establece una evaluación futura genuinamente prospectiva, pero **no demuestra todavía habilidad**. El rendimiento de 2028 deberá compararse con su propio horizonte y baseline, no sumarse con ACD o NEWCONF como si todos fueran un único endpoint.
