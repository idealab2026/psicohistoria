# PSICOHISTORIA · GED anual 2024: estabilidad de edición 25.1 → 26.1

**Protocolo fijado el 20-11-2026 antes de evaluar los registros de 2024 contenidos en GED 26.1 para este contraste.** Extensión *postselección* del resultado Candidate→GED del PR #151: **no es prueba independiente**, no contiene predicciones emitidas, y no sirve para optimizar retrospectivamente un clasificador. La primera etiqueta anual 2024 (GED 25.1) y sus diferencias respecto a Candidate ya se conocen. Lo nuevo es medir si esa **misma anualidad 2024** cambia al usar la versión GED 26.1. El riesgo de interpretaciones oportunistas se controla publicando todas las celdas de la cuadrícula, no una selección favorable.

## Pregunta

¿Cuánto cambia la clasificación binaria de un país de 2024 (y la suma de fallecidos que la origina) entre GED 25.1 y GED 26.1 si mantenemos exactamente el mismo universo de 196 países, la misma ventana y **el mismo conjunto en riesgo definido únicamente por Candidate Q1 2024**?

Este estudio distingue tres objetos distintos:

- **Candidate Q3 2024:** indicador provisional de mayo/julio.
- **GED 25.1:** primera edición anual de referencia que abarca 2024 en el estudio previo.
- **GED 26.1:** edición anual posterior que también contiene hechos de 2024 pero puede recodificarlos. **No estuvo disponible al comienzo de 2024**, y no se usa como origen de ninguna predicción.

Ni una versión GED ni la otra constituye la verdad completa e inmutable de un conflicto.

## Fuentes congeladas sin dependencia de cuenta privada

1. Dos ZIP originales oficiales UCDP: `https://ucdp.uu.se/downloads/ged/ged251-csv.zip` y `https://ucdp.uu.se/downloads/ged/ged261-csv.zip`. SHA-256 ya establecidos, antes de este estudio, en el PR #151: `e256f1fb20a579d8b2f910e5bae212f486d3002adaa2e4359ace740c737da05d` y `8c941d84954e555ee2e54f40fa04d9203bf1e2f962203d0a9930966c4947c667`.
2. La cohorte de 196 códigos y los 392 vectores país-año del informe original `data/candidate-to-annual-ged-resolution.json`; sus fechas, estados, hashes y datos primarios deben permanecer inalterados.
3. No se descargan, publican o utilizan registros personales; solo fuentes institucionales públicas con atribución UCDP (CC BY 4.0).

## Definiciones fijadas antes del nuevo cálculo

- **Año del evento = 2024, edición del ZIP = 25.1 o 26.1.** Leer `year=2024` de ambos CSV y descartar cualquier fila de otro año. No confundir el año del evento con el de la edición GED.
- **Tipo de violencia = 1** (estatal), `date_prec ∈ {1,2}`, `best` entero no negativo, `country_id` en el universo de 196.
- Ventanas exactas: 30 días (1–30 mayo) y 90 días (1 mayo–29 julio), sin prorratear eventos que atraviesan el límite.
- Para cada `T ∈ {1,5,10,25}`: solo países donde Candidate Q1 original registró `best < T` entre enero y marzo de 2024.
- Comparar GED 25.1 vs GED 26.1; en paralelo, Candidate Q3 vs GED 25.1 y vs GED 26.1 para mostrar cuánto se mueve la aparente calidad del indicador. **Ninguna nueva probabilidad se entrena ni emite.**
- Recuento de positivos en cada edición, coincidencia, primeras-solo, posteriores-solo, ambos-negativos, países que cambian y sumas `best` por país. Identificadores exactos de los mismos eventos se comparan *separadamente* como trazabilidad de codificación, no como confirmación factual.
- Publicar **todos** los umbrales × horizontes (ocho comparaciones), incluido el caso T=5/30d que motivó el estudio. Los detalles son retrospectivos y sujetos a selecciones previas.

## Gates técnicos

1. Rechazar ZIP con SHA o firma ZIP distintos, estructura anómala, ID repetidos, valores ilegibles, `best<0`, fecha invertida, precisión o tipo inválido.
2. La lectura de GED 25.1 debe reproducir **exactamente**, país a país para los 196 y ambos horizontes, el informe inmutable #151. Si discrepa, abortar antes de la comparación.
3. La comparación Candidate Q3 vs GED 25.1 debe reproducir **exactamente** cada matriz de confusión del informe anterior.
4. El riesgo no se calcula con GED 25.1 ni 26.1; procede de Candidate Q1 2024 del informe previo.
5. Reproducibilidad: pruebas sintéticas adversariales y CI independiente que descargue ambos originales cada vez; después de observar los resultados, fijar informe JSON y activar comparación exacta en CI.
6. Privacidad: lista explícita de nuevos archivos en `scripts/audit_public.py`; no referencias a otros repositorios ni cuentas.
7. Inmutabilidad: GEO2027, NEWCONF2027, ACD2027, GEO2028 y las 15 alertas no se modifican.

## Reglas de interpretación predefinidas

Si los positivos o sus sumas cambian entre GED 25.1 y GED 26.1, hay **inestabilidad intra-anual observada** y no basta resolver Candidate usando una única edición anual. Si las etiquetas son idénticas, ello apoya la estabilidad **solo para 2024, estos umbrales y esas dos ediciones**; no demuestra robustez para otras anualidades ni que el indicador mida todo el daño real.

No se propondrá un umbral alternativo seleccionado después de ver el resultado, no se llamará *precisión predictiva* a la coincidencia de etiquetas, no se interpretará un ID ausente como falsedad del acontecimiento, ni se confirmarán Kenia/Libia 2026 sin su GED anual. Esta extensión no establece la fecha original de disponibilidad de Candidate ni valida un uso operativo en tiempo real.

**Estado del protocolo inicial:** diseño e implementación previos al nuevo cálculo GED 26.1→eventos 2024; pendiente de la primera ejecución reproducible y congelación del informe resultante.
