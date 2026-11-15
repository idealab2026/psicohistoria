# Pre-registro GEO2028 · Nuevo año de origen 2026, horizonte 2

**Pre-registrado: 15 de noviembre de 2026, antes de contar con el cierre anual UCDP de 2026.** Este documento es la especificación pública del próximo origen temporal. **No contiene ni emite predicciones con origen 2026.** A esta fecha, el catálogo primario de UCDP sigue ofreciendo el dataset anual OrganizedViolenceCY **26.1 (1989–2025)** y la API declara la versión anual 26.1 vigente:

- Fuente oficial de versiones: https://ucdp.uu.se/downloads/
- Documentación de versiones de API: https://ucdp.uu.se/apidocs/

El dataset **UCDP Candidate Events mensual de 2026** es un producto distinto con criterios de edición y lag diferentes. **No puede sustituir al corte anual definitivo ni respaldar la etiqueta "origen anual oficial 2026".**

## 1. Pregunta exacta y cronología de emisión

Entre los gobiernos-país GWNO con registros oficiales válidos en **2025 y 2026** de la primera edición anual completa UCDP OrganizedViolenceCY **27.1**, ¿cuál es la probabilidad de que, durante el año **2028**, se registren **al menos 25 muertes de violencia organizada estatal** según la misma definición binaria empleada en GEO2027 y GEO2028 origen 2025?

| Comparación legítima | GEO2028 original ya emitida | GEO2028 nuevo origen preparado |
|---|---|---|
| Origen observado | **2025**, fuente 26.1 SHA original | **2026**, fuente anual 27.1 aún inexistente |
| Año objetivo | 2028 | 2028 |
| Horizonte | 3 años | 2 años |
| Estatus actual | **196 probabilidades emitidas 15/11/2026** | **0 probabilidades emitidas** |
| Cohorte | 196 GWNO del origen 2025 | Todos los GWNO con datos 2025+2026 del origen 2026, número **por determinar** |
| Población comparable | GWNO emitidos en 2025 | Intersección por ID GWNO, con altas/bajas registradas |
| Resultado 2028 | 0 etiquetas oficiales certificadas | 0 etiquetas oficiales certificadas |

**Advertencia central:** ambas emisiones tendrán exactamente el **mismo evento objetivo 2028** para cada GWNO compartido. Añadir un nuevo **origen** no añade una observación independiente de la verdad 2028. Sus diferencias pueden reflejar información nueva de 2026 **y** revisiones retrospectivas de 2025 y anteriores entre las ediciones UCDP 26.1 y 27.1. El generador contará y listará explícitamente los cambios de estado 2025, los países nuevos y los que dejan de pertenecer a la cohorte. No se atribuirá causalmente una mejora a "información nueva de 2026" sin separar ambos componentes.

## 2. Modelo y comparadores fijados ANTES de recibir 2026

**No se selecciona nuevamente un modelo tras examinar datos 2026.** Se traslada intacto el protocolo del **GEO2027 primario**, primera emisión con origen 2025 y horizonte dos años:

- Para cada país y el conjunto de países, contar todas las transiciones **de un año** de estado binario anual 0/1 con ambos años observados hasta 2026 (1989–2026).
- Calcular las transiciones globales con **Beta(1,1)**: \(q_s^{(G)}=(N_{s\to1}+1)/(N_{s\to0}+N_{s\to1}+2)\), para \(s\in\{0,1\}\).
- Calcular las transiciones regularizadas por país mediante **20 observaciones equivalentes globales**: \(q_s^{(c)}=(N_{c,s\to1}+20q_s^{(G)})/(N_{c,s\to0}+N_{c,s\to1}+20)\).
- Estado inicial: la **etiqueta oficial 2026** del país. Aplicar exactamente **dos pasos** del mismo kernel: \(p_1=q_{estado2026}\) y \(p_2=(1-p_1)q_0+p_1 q_1\).
- **Modelo principal:** p_model, Markov por país 2 pasos con shrink20.
- **Referencia principal:** p_baseline_global_5y, frecuencia conjunta Laplace(1) de estados activos entre **2022–2026**, restringida a los países del conjunto de riesgo 2026, con al menos 95 % de las 5 exposiciones por país documentadas.
- **Comparador secundario:** p_global_markov, dos pasos usando las probabilidades de transición globales.
- Predicciones redondeadas a **12 decimales**, probabilidades estrictamente interiores al intervalo (0,1), GWNO sin duplicados y en orden ascendente.

**Métrica principal futura, fijada aquí:** \(\Delta \mathrm{Brier}=\mathrm{Brier}(p_{modelo})-\mathrm{Brier}(p_{referencia})\), sobre la cohorte país-origen **emitida y posteriormente completamente resuelta**, sin modificarla. El signo negativo favorece al modelo en esa realización; no demuestra significación estadística general ni independencia entre países. Se registrarán Brier frente a Markov global, log-loss y calibración descriptiva por estado origen, solo cuando la procedencia de resultados futuros sea verificable. Prohibido bootstrap IID por países, p-valores artificiales y cambio automático de modelo.

El generador **reproduce exactamente la estimación de GEO2027 original en pruebas sintéticas** cuando se invoca con origen=2025: todos los vectores y cifras agregadas coinciden. Esta es una prueba de continuidad de fórmula, **no una evaluación retrospectiva con fuentes 2026**.

## 3. Fuente y separación pública entre protocolo, evidencia y emisión

**Fase A — AHORA (2026).** Fusionar en main este documento, el script scripts/prepare_geo2028_origin2026.py y sus pruebas; no crear data/forecast-2028-origin2026.json, no guardar en el repositorio datos futuros de 2026 ni resultados inventados. Debe existir un commit **anterior** a cualquier conocimiento de la edición anual 27.1.

**Fase B — CUANDO UCDP PUBLIQUE 27.1 (2027).** Revisar la existencia de su **primer dataset anual completo que incluya 2026** en la fuente primaria UCDP. Conservar un ZIP original 27.1 de OrganizedViolenceCY, calcular SHA-256 de **todos los bytes**, registrar URL oficial, fecha comprobada, licencia, número de registros, cobertura y enlace de publicación verificable. El generador solo acepta, de modo conservador, la ruta esperada
\`https://ucdp.uu.se/downloads/organizedviolencecy/organizedviolencecy-271-csv.zip\`.
Si el proveedor cambia la nomenclatura, abrir una modificación del contrato **motivada y fechada**, sin alterar a posteriori la definición del resultado ni los modelos. **Ningún operador puede declarar unilateralmente que el hash y su fecha prueban la primera publicación real**.

Crear mediante PR **un commit separado que fije el manifiesto con el SHA fuente antes de generar/preregisterar números**. La estructura requerida por el script es un objeto JSON:
\`\`\`json
{
  "schema": "idealab.psico.future_ucdp_2026_origin_source_pin.v1",
  "dataset": "UCDP OrganizedViolenceCY",
  "version": "27.1",
  "last_observed_year": 2026,
  "pin_status": "SOURCE_CANDIDATE_UNCERTIFIED",
  "first_release_independently_attested": false,
  "official_url": "https://ucdp.uu.se/downloads/organizedviolencecy/organizedviolencecy-271-csv.zip",
  "official_zip_sha256": "SHA-256 REAL DE 64 HEXADECIMALES",
  "publication_date_claimed": "AAAA-MM-DD"
}
\`\`\`
Es un ejemplo esquemático **no válido para emitir**: la huella y fecha deben sustituirse por evidencia real, no se incluye un hash inventado en el repositorio. La comprobación interna de estos campos es una verificación de coherencia, **no una notarización independiente**.

**Fase C — PRIMERA EMISIÓN EN 2027, ANTES de 2028.** Después de confirmar la fuente 27.1, ejecutar el generador contra el ZIP original y el manifiesto previamente fechado. El programa guarda un archivo **CANDIDATO NO EMITIDO fuera del repositorio** y no inicia automáticamente una PR, una publicación web o un resultado de modelo. Revisar su población y las revisiones 2025. Si es válido, abrir una PR **nueva y separada** que añada el JSON completo de probabilidades GEO2028 origen 2026. El primer commit público del documento completo debe producirse **antes del 01/01/2028 UTC** y registrar su SHA-256, commit, fecha real del servidor GitHub y las fuentes. Nada puede sobrescribir la primera emisión GEO2028 origen 2025 ni las 424 preguntas originales de 2027.

**Si 27.1 no está disponible o no puede autenticar su primera publicación anual completa antes del 01/01/2028, NO EMITIR ni backdatear.** La aparición de un archivo 28.1 posterior no le convierte retroactivamente en un origen 2026 genuinamente disponible en 2027.

## 4. Bloqueos técnicos verificables

- No aceptar ZIP de la edición 26.1, 28.1, de GED mensual o de otra fuente.
- No aceptar una versión autodeclarada sin **SHA de bytes del ZIP** coincidente; URL solo HTTPS del dominio oficial exacto y ruta preestablecida.
- No aceptar fecha autodeclarada antes del 01/01/2027, posterior a la fecha actual o un intento de emisión en 2028 o después.
- No aceptar **ninguna fila con año mayor que 2026**, valores negativos/no numéricos, duplicados país-año, cambio de nombre dentro de la misma edición, encabezados duplicados, CSV con tamaño insuficiente o mortalidad estatal inexistente/ambigua.
- Mantener la población prospectiva **dinámica**: 190–210 GWNO con registros tanto en 2025 como en 2026. No suponer exactamente 196 porque esa era la cohorte de **otra edición**; bloquear una cobertura claramente anómala.
- No imputar ausencia de filas de país 2026 como estado 0 ni eliminar silenciosamente los países revisados.
- No modificar ni sustituir la primera emisión GEO2028 origen 2025. El generador exige y comprueba su procedencia a partir del código de auditoría institucional antes de una ejecución real.
- El archivo de salida solo puede escribirse **fuera del repositorio**. Su estado siempre será **UNISSUED_CANDIDATE_DO_NOT_CLAIM_PUBLIC_FORECAST** y su contador de probabilidades públicamente emitidas, **0**.

La CI de Idea Lab ejecuta únicamente escenarios **sintéticos** que prueban estas prohibiciones, además de cotejar bit a bit la metodología con la estimación GEO2027 anterior. No descarga 27.1 ni crea predicciones con origen 2026 hoy.

## 5. Avance real versus resultado

Esta iteración añade un **pre-registro temporal antes de recibir el nuevo año de origen**, que es científicamente más exigente que preparar todo después de observar los datos. Todavía **no aumenta** las **620 preguntas** públicas ya emitidas ni las **0 etiquetas futuras certificadas**. La futura emisión 2026→2028, aun siendo una nueva oportunidad de actualizar el pronóstico, seguirá compartiendo el objetivo 2028 con GEO2028 origen 2025 y se evaluará de forma emparejada, evitando presentar ambos resultados como réplicas independientes.

**Pendiente indispensable, fuera de nuestro control:** la primera edición oficial y completa de 2026 publicada por UCDP en 2027.
