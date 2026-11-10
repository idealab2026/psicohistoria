# PSICOHISTORIA · Protocolo cerrado antes de la emisión GEO-2027-01

**Estado:** protocolo metodológico preregistrado; **NO constituye todavía una predicción emitida**. Debe fusionarse en \`main\` antes de producir y publicar la lista completa de probabilidades. No ajustar después de observar los resultados del generador ni cambiar el modelo durante 2027.

## Pregunta, tiempo, unidad y procedencia

- **Pregunta prospectiva independiente:** para cada país de la cohorte UCDP en 2025, ¿el campo de fallecimientos estimados por violencia organizada *state-based* supera o alcanza 25 durante el año natural **2027**? No es el indicador \`onset2\` de inicio de guerras; no equivale a "violencia gubernamental contra civiles".
- **Fuente de entrada:** fichero oficial UCDP OrganizedViolenceCY **26.1** (año observado más reciente: 2025). URL literal \`https://ucdp.uu.se/downloads/organizedviolencecy/organizedviolencecy-261-csv.zip\`; SHA-256 **\`66910888f5653af42776d2debc1d72fe527559e7f7fc82e69b7c8771467f2d34\`**. Fuente protegida por hash; rechazar cualquier diferencia.
- **Variable operacional**: \`sb_total_deaths_best\` o su alias \`sb_total_deaths_best_cy\` de la edición 26.1; \`Y=1\` si el valor es mayor o igual que 25; \`Y=0\` si es menor. No interpretar ausencia de país-año como cero.
- **Universo invariable:** 196 códigos Gleditsch-Ward \`country_id\` que tengan información para 2024 y 2025 en la edición congelada. Un país futuro renombrado o desaparecido conserva el código original; se informa la pérdida de correspondencia, sin inventar etiquetas ni redefinir la cohorte.
- **Fecha de corte:** 31-12-2025. Prohibido incorporar cualquier evento de 2026/2027, información posterior a esta versión de origen, o revisiones del archivo.
- **Emisión:** únicamente cuando una PR institucional publique **todas** las probabilidades por país y sus referencias en GitHub antes de 01-01-2027. La primera marca observable es el commit público que contenga los bytes íntegros, no la fecha de generación. GitHub proporciona trazabilidad pública por commit y SHA-256; **no equivale a sellado de tiempo externo independiente**.
- **Fuente para resolución:** la **primera** edición oficial completa de UCDP OrganizedViolenceCY que cubra el año 2027, publicada después de finalizarlo. No presumir que existe ni que se llamará 28.1. Fijar URL, hash, fecha de descarga y cobertura al resolver; las ediciones revisadas posteriores solo servirán para sensibilidad diferenciada.

## Modelos congelados

Se construye un indicador binario por país-año \`S(c,t)=1[best_deaths(c,t)>=25]\` desde 1989 hasta 2025. Solo se cuentan pares anuales consecutivos disponibles para estimar transiciones.

Para estado anterior \`s∈{0,1}\`:

- Transición global suavizada \`q_g(s)=(N_g[s→1]+1)/(N_g[s→0]+N_g[s→1]+2)\` (prior de Laplace 1).
- Transición por país \`q_c(s)=(N_c[s→1]+20*q_g(s))/(N_c[s→0]+N_c[s→1]+20)\` (shrinkage fijo 20).
- **Modelo primario:** empezando en el estado observado de 2025, se aplica dos veces la matriz de transiciones propia del país. Si \`p_2026=q_c(S(c,2025))\`, entonces \`p_2027=(1-p_2026)*q_c(0)+p_2026*q_c(1)\`.
- **Referencia principal:** tasa global suavizada de estados positivos en la misma cohorte, años 2021–2025, \`(positivos+1)/(observaciones+2)\`, idéntica en todos los países.
- **Referencia secundaria:** Markov global de dos pasos desde el estado 2025, calculado con \`q_g\`.

Los tres valores por país se redondean a **12 decimales** antes de publicarse y son inmutables al evaluar.

## Evaluación, sin cambiar reglas después

- **Métrica primaria:** Brier de probabilidades por país congeladas, comparado con el Brier del baseline global de cinco años (diferencia modelo − referencia). Mejora si es negativa.
- **Secundarias:** log-loss con truncado numérico explícito para evitar log(0), Brier frente a Markov global, bandas de calibración descriptivas y diferencias con bootstrap por país (2.000 remuestreos); se comunican todos los resultados, incluidos los desfavorables.
- **Cobertura:** reportar emitidos, resueltos y pendientes; país-año ausente del fichero de resolución sigue pendiente, nunca negativo. Si la resolución cubre menos del 95 % de la cohorte, bloquear cualquier afirmación de capacidad.
- **Control:** comparar exactamente contra las probabilidades **publicadas** y el protocolo SHA-256, no volver a ajustar el modelo con los datos 2027.
- **Limitaciones:** clasificación binaria con umbral de 25 y horizonte a dos años; no mide inicio de guerra, severidad por encima del umbral ni violencia del gobierno contra civiles. Sin validación histórica prospectiva previa; las probabilidades son **exploratorias**, no decisiones operativas.

El código institucional de generación y las pruebas adversariales están en \`scripts/forecast_2027_statebased.py\` y \`scripts/test_forecast_2027_statebased.py\`. Los ficheros de pronóstico se distribuirán en Pages únicamente tras registrar la primera emisión pública verificable; nunca se usan fuentes personales.
