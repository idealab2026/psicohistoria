# PSICOHISTORIA · Túnez: atribución de revisiones GED a probabilidades GEO H2

**Protocolo registrado el 17 de noviembre de 2026, antes de observar los resultados del nuevo experimento.** Análisis retrospectivo de sensibilidad mecánica de fuentes, **no** pronóstico emitido en 2019 ni 2022, ni prueba causal de error predictivo.

## Problema

La auditoría de cinco ediciones UCDP GED ha demostrado que en Túnez, GWNO 616, la fuente GED21.1 codificaba **0, 0 y 17** muertos estatales en 2013–2015, mientras que GED22.1 registra **29, 51 y 75**. Estas tres revisiones cruzan el umbral binario GEO de 25 fallecidos. Pueden modificar las transiciones históricas de los modelos incluso aunque el año de origen de evaluación no cambie.

La pregunta no es si la violencia histórica cambió: **cambió la medición publicada**. Mediremos cuánto afectan esos cambios a las probabilidades reconstruidas de dos años de horizonte, manteniendo absolutamente fijos los algoritmos existentes.

## Dos comparaciones distintas

**A. Origen ficticio 2019 → año objetivo 2021.** Recuperar GED20.1/21.1/22.1/23.1, reconstruir para los 196 GWNO el mismo indicador de violencia estatal: suma GED tipo 1 de `best` por país y año. Entrenar exactamente hasta el **origen 2019** tanto el modelo binario original (Laplace 1, shrinkage global 20) como el Markov de cuatro estados con parámetros fijos. Las ediciones GED21.1/22.1/23.1 se publicaron después del origen simulado; este ejercicio **NO es un backtest verdaderamente contemporáneo**.

Se realizará una **descomposición Shapley exacta de cuatro factores**, con las 16 coaliciones posibles, entre GED21.1 y GED22.1: las revisiones de Túnez 2013, 2014 y 2015 se tratan individualmente; el cuarto factor son **todas las demás modificaciones** de los datos de entrenamiento entre las dos ediciones, incluidas otras posibles revisiones de Túnez. La suma de efectos de los cuatro factores debe reproducir exactamente la variación total de probabilidad H2 en la escala del modelo. Son **contribuciones algebraicas por edición**, no efectos causales atribuibles a conflictos históricos. La descomposición se calcula por separado para el modelo binario y el de cuatro estados; no se elige a posteriori el que mejor funciona.

**B. Origen retrospectivo 2022 → resultado oficial UCDP 2024.** Tomar el archivo OrganizedViolenceCY23.1 **original y verificado por SHA-256**, preprocesar con los modelos fijos y generar la probabilidad reconstruida del país en 2024. Repetir el cálculo con un conjunto **hipotético** que conserva todo UCDP23.1 salvo las tres filas de Túnez 2013–2015, sustituidas por sus valores de GED21.1. Comparar las probabilidades y los errores cuadrados individuales respecto a la etiqueta 2024 de OrganizedViolenceCY25.1. No se denominan predicciones retrospectivamente emitidas: una base híbrida de ese tipo **nunca fue una edición oficial**.

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
