# PSICOHISTORIA · Túnez: atribución de revisiones GED a probabilidades GEO H2

**Protocolo registrado el 17 de noviembre de 2026, antes de observar los resultados del nuevo experimento.** Análisis retrospectivo de sensibilidad mecánica de fuentes, **no** pronóstico emitido en 2019 ni 2022, ni prueba causal de error predictivo.

## Problema

La auditoría de cinco ediciones UCDP GED ha demostrado que en Túnez, GWNO 616, la fuente GED21.1 codificaba **0, 0 y 17** muertos estatales en 2013–2015, mientras que GED22.1 registra **29, 51 y 75**. Estas tres revisiones cruzan el umbral binario GEO de 25 fallecidos. Pueden modificar las transiciones históricas de los modelos incluso aunque el año de origen de evaluación no cambie.

La pregunta no es si la violencia histórica cambió: **cambió la medición publicada**. Mediremos cuánto afectan esos cambios a las probabilidades reconstruidas de dos años de horizonte, manteniendo absolutamente fijos los algoritmos existentes.

## Dos comparaciones distintas

**A. Origen ficticio 2019 → año objetivo 2021.** Recuperar GED20.1/21.1/22.1/23.1, reconstruir para los 196 GWNO el mismo indicador de violencia estatal: suma GED tipo 1 de `best` por país y año. Entrenar exactamente hasta el **origen 2019** tanto el modelo binario original (Laplace 1, shrinkage global 20) como el Markov de cuatro estados con parámetros fijos. Las ediciones GED21.1/22.1/23.1 se publicaron después del origen simulado; este ejercicio **NO es un backtest verdaderamente contemporáneo**.

Se realizará una **descomposición Shapley exacta de cuatro factores**, con las 16 coaliciones posibles, entre GED21.1 y GED22.1: las revisiones de Túnez 2013, 2014 y 2015 se tratan individualmente; el cuarto factor son **todas las demás modificaciones** de los datos de entrenamiento entre las dos ediciones, incluidas otras posibles revisiones de Túnez. La suma de efectos de los cuatro factores debe reproducir exactamente la variación total de probabilidad H2 en la escala del modelo. Son **contribuciones algebraicas por edición**, no efectos causales atribuibles a conflictos históricos. La descomposición se calcula por separado para el modelo binario y el de cuatro estados; no se elige a posteriori el que mejor funciona.

**B. Origen retrospectivo 2022 → resultado oficial UCDP 2024.** Tomar el archivo OrganizedViolenceCY23.1 **original y verificado por SHA-256**, preprocesar con los modelos fijos y generar la probabilidad reconstruida del país en 2024. Repetir el cálculo con un conjunto **hipotético** que conserva todo UCDP23.1 salvo las tres filas de Túnez 2013–2015, sustituidas por sus valores de GED21.1. Comparar las probabilidades y los errores cuadrados individuales respecto a la etiqueta 2024 de OrganizedViolenceCY25.1. No se denominan predicciones retrospectivamente emitidas: una base híbrida de ese tipo **nunca fue una edición oficial**.

## Resultados reales con las fuentes oficiales SHA-verificadas

### 1. Origen histórico fijo 2019 → objetivo 2021 (H2)

La suma de eventos estatales GED, agregados por GWNO×año, reproduce los siguientes fallecidos de Túnez (GWNO 616):

| Año | GED20.1 | GED21.1 | GED22.1 | GED23.1 |
|---|---:|---:|---:|---:|
| 2013 | 0 | 0 | 29 | 29 |
| 2014 | 0 | 0 | 51 | 51 |
| 2015 | 4 | 17 | 75 | 75 |

Se han construido cuatro historiales completos de los mismos 196 GWNO. La fecha de origen de **todos** los ajustes es 2019; las fuentes posteriores se han truncado en 2019, aunque sus valores anteriores a ese año puedan contener revisiones conocidas después. Por eso se trata de un *pseudo-origen* de diagnóstico, **nunca de un pronóstico emitido en 2019**.

| Edición que reconstruye el historial | H2 Markov binario | H2 Markov cuatro estados |
|---|---:|---:|
| GED20.1 | 5,8099 % | 30,3885 % |
| GED21.1 | 5,8057 % | 31,8558 % |
| GED22.1 | 6,2767 % | 30,9748 % |
| GED23.1 | 6,2745 % | 31,2140 % |

Al comparar GED21.1 con GED22.1 para el origen fijo de 2019, el modelo binario sube **+0,4711 puntos porcentuales**; el modelo de cuatro estados baja **−0,8810 puntos**. El estado de origen de Túnez no cambia en ninguna de esas ediciones: es binariamente inactivo (`best<25`), aunque con una intensidad positiva de 1–24 víctimas.

### 2. Atribución matemática exacta de los cambios GED21.1→GED22.1

Se han ejecutado las **16 coaliciones** de cuatro factores, con efectos Shapley, ajustando todo el modelo después de cada sustitución de fuente (incluyendo los recuentos de transición globales). La suma telescópica se verifica a precisión de 10⁻¹⁰.

| Factor de revisión | Efecto en binario, pp | Efecto en 4 estados, pp |
|---|---:|---:|
| Túnez 2013, 0→29 | **+1,8482** | **+2,1054** |
| Túnez 2014, 0→51 | +0,1396 | +0,3414 |
| Túnez 2015, 17→75 | **−1,5202** | **−1,5191** |
| Todas las demás revisiones del histórico | +0,0035 | **−1,8088** |
| **Variación total de probabilidad** | **+0,4711** | **−0,8810** |

Importante: se trata de la **atribución algebraica de diferencias entre conjuntos de datos** manteniendo un algoritmo fijo, no una estimación causal del efecto real de los acontecimientos en Túnez. Las ediciones comparten información y países; no son muestras independientes.

### 3. Origen 2022 → desenlace oficial 2024 de Túnez

En la combinación histórica ya evaluada `OrganizedViolenceCY23.1 (hasta 2022) → UCDP25.1 (2024)`, el desenlace para Túnez es **0 fallecidos estatales**. Esto implica un resultado binario **inactivo** bajo la definición de GEO `best>=25`.

Se reconstruye la probabilidad con UCDP23.1 sin modificaciones y, separadamente, con un **conjunto contrafactual** que conserva todos los demás datos pero sustituye los recuentos de Túnez de 2013–2015 por las tres cifras de GED21.1 (0, 0, 17).

| Algoritmo H2 | UCDP23.1 original | Contrafactual con las tres filas antiguas | Cambio de la revisión |
|---|---:|---:|---:|
| Markov binario | **5,8888 %** | 5,4731 % | +0,4157 pp |
| Markov cuatro estados | **29,9332 %** | 27,4853 % | +2,4480 pp |

Dado que el resultado verdadero según UCDP25.1 es 0, los errores cuadrados individuales del modelo binario son **0,00346782** y **0,00299552** respectivamente; en cuatro estados **0,08959972** y **0,07554393**.

**Diagnóstico editorial esencial:** en este caso **no existió un fallo de clasificación binaria del Markov original usando el umbral 0,5**: la probabilidad original de suceso era 5,89 % y el resultado fue 0. Las revisiones de 2013–2015 cambiaron la magnitud de la probabilidad, pero **no explican por qué habría fallado la clasificación de Túnez en 2024**, porque esa clasificación no falló bajo el criterio especificado. Un resultado de un único país y año tampoco demuestra qué modelo generaliza mejor.

### 4. Advertencia sobre el histórico anterior a 2011

Al comprobar el tramo 1989–2019, GED23.1 agregado coincide **numéricamente en todas las filas comparables** de OrganizedViolenceCY23.1 de la cohorte, pero hay **128 país-años del panel GED reconstruido que no figuran como filas de Country-Year23.1** (el panel GED asigna 0 únicamente cuando esa edición no registra un evento estatal en el país-año). Por tanto, el modelo reconstruido con GED para el pseudo-origen 2019 no es estrictamente el mismo panel de exposición del modelo oficial Country-Year: **los ceros de relleno son un supuesto de modelado y no pueden interpretarse como observaciones de ausencia de violencia**. El experimento cuantifica cambios *dentro de la misma convención GED*; no convierte esa convención en identidad completa con el conjunto original para 1989–2010.

En cambio, la reconstrucción histórica de origen **2022** utiliza íntegramente el Country-Year23.1 original, con sus países históricos y exposiciones globales, de modo que el contrafactual altera únicamente las tres filas explícitas de Túnez.

## Validación y limitaciones

1. Se usan únicamente archivos originales GED20.1/21.1/22.1/23.1 y las dos ediciones Country-Year23.1/25.1 fijadas por SHA-256; sus hashes se heredan de los informes previos.
2. La edición GED23.1 debe reproducir **exactamente los 2.352 country-years** originales de OrganizedViolenceCY23.1 para 2011–2022; la concordancia antes de 2011 se audita por separado porque también participa en el entrenamiento.
3. Todo entrenamiento se trunca al origen histórico; el modelo original mantiene la cohorte congelada de 196 GWNO y el horizonte H2.
4. Se comprobó en los análisis anteriores que GED19.1 excluía Siria; aquí únicamente se utilizan GED20.1 y posteriores, con su cobertura posterior documentada, aunque otras ausencias por cobertura no certificadas siguen siendo una limitación.
5. Los diagnósticos de Brier **para un solo país y un solo año** no permiten hablar de significación estadística ni generalización; un cambio de error tampoco demuestra que una revisión fuera la **causa real** del fallo del modelo.
6. No se cambian, recrean ni sustituyen las predicciones GEO2027/GEO2028, ni sus alertas, ni se conocen resultados de 2027.

## Artefactos

Código: `scripts/experiment_geo_ged_tunisia_2013_15_attribution.py`.

Pruebas de integridad, recorte temporal y telescopaje Shapley: `scripts/test_experiment_geo_ged_tunisia_2013_15_attribution.py`.

Informe reproducible oficial: `data/geo-ged-tunisia-2013-15-h2-attribution.json`.

CI exclusiva y puerta obligatoria de GitHub Pages: `.github/workflows/geo-ged-tunisia-h2-attribution.yml` y `pages.yml`.

**Criterio para el paso siguiente:** después de ver el signo y el tamaño de cada factor, determinar si las revisiones explican una parte apreciable de la probabilidad de Túnez para 2024. Si la variación es pequeña, concluir expresamente que **no explica** el desacierto histórico; no forzar ninguna narrativa.
