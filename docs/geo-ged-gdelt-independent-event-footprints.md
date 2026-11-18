# GEO H2 — Auditoría independiente de huellas mediáticas de acontecimientos

**Diseño fijado el 18/11/2026, antes de observar los resultados de GDELT.**

## Pregunta y límites

Los cambios de estado inicial entre cero muertes y 1–24 observados para Ruanda (2021), Burundi (2022) y Venezuela (2021) originaron variaciones grandes de las probabilidades del modelo H2. Las revisiones internas de UCDP no identifican la verdad latente; el indicador de estabilidad política del Banco Mundial muestra concordancia contextual pero no cuenta fallecidos.

La primera prueba externa por acontecimiento usa:
- **UCDP GED 25.1** (misma institución que OrganizedViolenceCY, no fuente independiente) para seleccionar **únicamente eventos de violencia estatal (type_of_violence=1)** con identificadores, intervalos de fecha, país, coordenadas y estimación puntual de muertes. El modelo original usa la variable country-year **sb_total_deaths_best**, por lo que otras categorías (2: no estatal y 3: unilateral) NO son elegibles para esta auditoría del umbral.
- **GDELT Events 1.0**, archivos diarios originales de eventos codificados desde noticias. Es independiente institucionalmente de UCDP, pero **puede compartir los mismos medios originales**. GDELT no es un censo independiente de víctimas.

No se mide si el recuento de muertes es verdadero; se comprueba si, en una muestra de episodios geolocalizados de UCDP GED, hay **huellas mediáticas cercanas de acciones violentas** codificadas por GDELT.

## Casos y muestreo congelados

Se fijaron los tres casos a partir del informe de revisiones 23.1→24.1→25.1, sin usar resultados de GDELT para escogerlos:

| GWNO | País | Año | Revisión origen |
|---|---|---:|---|
| 517 | Ruanda | 2021 | 23.1→24.1 |
| 516 | Burundi | 2022 | 23.1→24.1 |
| 101 | Venezuela | 2021 | 24.1→25.1 |

Se descarga exclusivamente el archivo oficial GED 25.1 y se retienen los eventos **state-based (tipo 1)** de estos GWNO y años con fecha puntual exacta, coordenadas válidas y al menos 1 fallecido estimado. Los registros GED de tipos 2/3 se contabilizan como excluidos, incluso si muestran más muertes. El experimento original no predice todas las modalidades de violencia. Para evitar selección retrospectiva basada en la coincidencia con GDELT, se escogen **como máximo dos fechas distintas por país-año**, dando prioridad al evento con mayor estimación `best` de muertes; los empates se resuelven por fecha e identificador. Si no hay ningún evento GED elegible, se registra expresamente como ausencia de evidencia GED seleccionable, **no** como ausencia de episodios reales.

## Comparación y falsos positivos

Se consultan archivos diarios oficiales de GDELT 1.0 para **el día de cada evento seleccionado y el día siguiente**, con SHA-256 de cada ZIP. Se filtra por códigos geográficos FIPS de GDELT (Ruanda RW, Burundi BY, Venezuela VE), el campo `SQLDATE` igual al día del evento GED, y acciones violentas CAMEO raíz **18, 19 o 20**. Se calculan coincidencias espaciales de **≤25 km** y **≤100 km** mediante haversine. Las noticias sobre acciones no violentas de la misma fecha y radio se enumeran como control de falsos positivos. Cada resultado ofrece identificadores GDELT cercanos, distancia y raíz CAMEO; **no** se equiparan automáticamente dos IDs como el mismo evento.

Ni una coincidencia acredita el número de víctimas, ni la falta de coincidencia descarta el evento: GDELT puede omitir noticias, localizar mal o codificar otra acción; además, el archivo descargado representa una ventana limitada de publicación.

## Limitaciones de interpretación

1. **Muestra dirigida**, no representativa del universo GED: tres casos problemáticos y un máximo de dos eventos principales de violencia estatal por caso. Los registros de violencia no estatal o unilateral no se usan como validación sustitutiva.
2. **Selección por mayor estimación de fallecidos:** introduce sesgo hacia episodios destacados; es una prueba de factibilidad, no una estimación de recall de GDELT.
3. **Independencia institucional incompleta:** pueden existir fuentes periodísticas compartidas.
4. **Diferencia ontológica:** GDELT codifica noticias/acciones mediante CAMEO; UCDP GED codifica episodios con muertes. La correspondencia individual debe verificarse antes de declarar "confirmación".
5. **Edición posterior al año histórico:** GED 25.1 no estaba disponible en 2021/2022. No se trata de validación prospectiva ni de evidencia contemporánea congelada.

La siguiente fase requerirá fuentes primarias y contraste documental manual, o una extracción legítima y autorizada de ACLED con una rúbrica de correspondencias y revisión humana. Según la [documentación oficial de ACLED](https://acleddata.com/api-documentation/getting-started), la API requiere credenciales OAuth de usuario. [GDELT Event Codebook](https://data.gdeltproject.org/documentation/GDELT-Data_Format_Codebook.pdf) y [archivos históricos GDELT](https://data.gdeltproject.org/events/) documentan la codificación externa.

## Contrato reproducible

Se exige SHA-256 oficial de GED25.1 y de cada archivo GDELT utilizado, archivo GED ZIP íntegro, GDELT correctamente delimitado por tabuladores, cohorte y casos congelados mediante informe anterior, comparación de fechas y distancias estricta, pruebas negativas de falsos emparejamientos, auditoría pública y preservación de GEO2027/GEO2028. El informe `data/geo-ged-gdelt-external-event-footprint-3case.json` quedará congelado tras ejecución y reproducción de CI.

No se ajustan parámetros predictivos, ni se reemiten probabilidades.
