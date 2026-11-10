# PSICOHISTORIA · IDEA LAB

Laboratorio público de investigación de sistemas complejos, fenómenos colectivos y evaluación de pronósticos.

**Estado actual: versión pública experimental, reconstruida de forma independiente.** El sitio incluye diez vistas navegables con formato oscuro, mapa de investigación, explorador de escenarios, evaluación probabilística, registro y hoja de ruta, y herramientas locales de preparación de hipótesis y guiones.

## Navegación

| Grupo | Vistas | Función pública |
| --- | --- | --- |
| Inicio | Resumen | Estado, líneas científicas y siguientes pasos |
| Predicciones | Explorador; Riesgos 2027 | Árbol sintético, supuestos y protocolo de emisión |
| Investigación | Mapa; Líneas y fuentes; Evidencia; Registro; Hitos | Estudios de demostración, Brier score, baselines y trazabilidad |
| Crear | Catálogo recuperado; Nuevas ideas; Estudio audiovisual | Cartera histórica institucional depurada (9 proyectos, 14 relaciones), borradores locales y guion de texto |

**Investigación institucional:** siete líneas de preguntas científicas con fuentes primarias, comparadores y condiciones pendientes. El CSV local permite comprobar fórmulas y un orden temporal declarado; la fecha real de publicación no se certifica y no existe evidencia de utilidad predictiva prospectiva.

**Catálogo de ideas recuperado:** proviene del archivo histórico aportado al proceso de migración. Se publican nueve proyectos (cuatro vertientes V1–V4, tres aplicaciones y dos fichas de estructura), ocho fichas documentadas y catorce relaciones. La publicación usa una **proyección de campos permitidos**: elimina rutas, enlaces a PR antiguos, identificadores personales y referencias de implementación heredadas. Sus estados y fechas son históricos, no acreditan ejecución actual, nuevos experimentos ni pronósticos.

**Límites de esta versión:** no contiene los históricos reales, catálogos de países, predicciones de cohortes, modelos calibrados con observaciones oficiales ni los componentes de generación audiovisual. Tampoco permite escritura en un backend: las ideas se generan en memoria y pueden exportarse localmente. Ninguna cifra sintética es una previsión real.

## Cuaderno de investigación desde la web

La nueva ruta pública `/trabajo.html` ofrece una **herramienta local de investigación**, separada del conjunto sintético de divulgación. Permite importar archivos JSON privados elegidos por el usuario y verificar sus hashes SHA-256 en memoria, crear hipótesis no emitidas y exportar un cuaderno JSON. La política CSP bloquea las conexiones de red en esa ruta; el cuaderno **no lee Google Drive, no emite predicciones, no hace sellados RFC3161 y no es la custodia institucional canónica**. Para preservar una nueva actividad debe exportarse y admitirse explícitamente en el archivo institucional privado. No se almacena contenido privado en GitHub Pages ni en el repositorio.

### Comparación histórica por país

En el cuaderno `/trabajo.html` se puede importar un archivo JSON local que contenga los catálogos originales retrospectivos 2016 (195 países) y/o 2020 (196 países), ya sea en `futuresCatalogs` o dentro de las notas experimentales del archivo canónico de once tablas. Un validador rechaza catálogos parciales, variantes con metadatos inconsistentes y cualquier intento de tratarlos como emisiones prospectivas.

El panel **Árbol predictivo · comparación entre países** superpone de uno a seis países con colores, trazos y leyendas diferentes, compara las probabilidades anuales para el fenómeno seleccionado y permite inspeccionar sus cuatro estados `00/01/10/11`. El modelo por defecto utiliza conteos específicos de cada país con regularización global (`country_shrinkage`); otros modelos pueden coincidir exactamente para países con igual estado de origen y eso se representa sin alterar los resultados. Los gráficos se calculan únicamente en memoria desde los archivos que aporta el usuario; no se suben países, trayectorias ni probabilidades privadas a GitHub Pages o Drive. Son resultados **retrospectivos sobre una edición revisada**, no emisiones acreditadas ni evidencia de habilidad prospectiva.

## Árbol de países sin importaciones manuales

La vista **Predicciones → Explorador** utiliza desplegables de **Sociedad, Pregunta, Origen, Modelo y Año**. Obtiene automáticamente un fichero estático de distribución pública, generado en CI desde el **CSV oficial UCDP OrganizedViolenceCY 26.1** (CC BY 4.0, 7.132 filas), con la edición y la suma SHA-256 documentadas. El script `scripts/build_official_countries.py` computa por separado los conteos de transición a partir de los países presentes en cada fecha de corte (2014 y 2018): no carga expedientes del laboratorio privado, no usa resultados después del corte para ajustar parámetros, y no traslada identificadores ni textos de archivos personales. El resultado reproducible está disponible como `/data/countries-ucdp261.json` solo en GitHub Pages, nunca en el historial fuente.

**Distinción científica fundamental:** estos árboles son **reconstrucciones retrospectivas con la edición UCDP 26.1, publicada en 2026**, no predicciones prospectivas emitidas en 2016/2020 ni una copia certificada de los catálogos históricos privados. Para comparar cifras exactas del registro sellado original hay que seguir utilizando la custodia privada institucional.

## Inspección de ediciones históricas UCDP (10-11-2026)

La fuente oficial publica un índice de ediciones históricas del conjunto **Intrastate Country Level Onset**. La utilidad `scripts/inspect_ucdp_archives.py` inspecciona dicho índice, lista las rutas efectivamente enlazadas y valida las ediciones 23.1 y 25.1 frente a sus hashes SHA-256 registrados. Produce solo estadísticas de metadatos (esquema, cobertura temporal, recuentos y hash), sin datos personales ni historiales por país. La inspección se ejecuta en un job independiente de PR y **no** forma parte de GitHub Pages.

**Restricción de inferencia**: la existencia actual de un archivo de edición antigua no prueba cuándo exactamente fue publicado ni si una versión 22.1 estaba disponible antes de 2023. Sin prueba de disponibilidad previa, un estudio a posteriori sigue siendo una comparación *cross-release* retrospectiva. No se certifica emisión prospectiva.

**Hallazgo reproducido en GitHub Actions 10-11-2026, ejecución 42848508792**: los CSV oficiales UCDP Onset 23.1 (12.161 país-año, hasta 2022) y 25.1 (12.553, hasta 2024) coinciden con las huellas SHA-256 institucionales. Comparando únicamente los 12.161 país-año hasta 2022, `onset2` cambia en **2 casos** (2018, 0→1; 2021, 1→0). No cambian la cobertura de países-año en el periodo común ni los **242** positivos agregados, aunque sí la identidad temporal de dos etiquetas. 1946–1989: 0 cambios; 1990–2009: 0; 2010–2020: 1; 2021–2022: 1.

El índice oficial incluye el CSV 24.1, pero su URL respondió **HTTP 404** en el job de investigación; la edición 22.1 no aparece enlazada. Este estado refleja únicamente esa comprobación puntual y puede cambiar si UCDP repara el archivo. Por ello **aún no es posible certificar una evaluación multianual point-in-time** usando la cadena de fuentes Onset prevista. El resultado de revisiones se publica en la sección *Investigación → Evidencia*, separado de las pruebas sintéticas y de la validación de capacidad predictiva.


## Q-GEO-01 · Contraste real entre ediciones 2017/2022 (10-11-2026)

La herramienta institucional `scripts/run_legacy_vintage_holdout.py` calcula, sin descargar ni publicar datos del repositorio personal, un experimento **ex post** con tres CSV históricos oficiales UCDP verificados por SHA-256. Ajusta tasas globales y por país (regularización 20) desde 2000 hasta el último año **realmente contenido** en cada archivo, sin utilizar las etiquetas del año objetivo durante el entrenamiento. Compara 2020–2022 (archivo enlazado bajo Onset 19.1 → resultados de 23.1) y 2024 (23.1 → 25.1).

| Año | Países-año | Inicios `onset2` |
|---|---:|---:|
| 2020 | 173 | 2 |
| 2021 | 173 | 1 |
| 2022 | 173 | 3 |
| 2024 | 196 | 1 |
| **Total** | **715** | **7** |

**Resultado negativo**: Brier del modelo por país **0,011100848419**, baseline de frecuencia global **0,010190138316**, referencia trivial siempre cero **0,009790209790**; Brier Skill frente a global **−8,94 %**. Log-loss del modelo **0,067702071233**, global **0,064953305637**. El intervalo exploratorio mediante 2.000 bootstrap por país para Brier país menos global fue **[+0,000199329, +0,001657918]**. Esto no permite afirmar superioridad y no constituye validación confirmatoria.

**Limitaciones materiales que no deben ocultarse:** el CSV que UCDP enlaza bajo 19.1 termina realmente en **2017**, aunque su codebook se refiere a 2018. Contiene **47 claves país-año duplicadas**, 13 con `onset2` contradictorio. Se aplicó una transformación OR («al menos un inicio») y, como sensibilidad exploratoria post hoc, se excluyeron todas las claves duplicadas: 516 observaciones, Brier Skill **−7,43 %**. La limpieza modifica la población al perder un país de referencia; no se presenta como prueba confirmatoria. No hay certificación criptográfica de las fechas de publicación originales, ni se garantiza paridad completa de las definiciones entre ediciones, ni se emitieron pronósticos en los años objetivo.

Experimento reproducible: ejecución de Actions `42856960583`, pruebas `scripts/test_run_legacy_vintage_holdout.py` y estudio agregado `data/research.json` (`external_vintage_holdout`). La web solo publica métricas agregadas, fuentes y advertencias. **Pronósticos prospectivos verificados: 0**.

## Evaluación temporal Q-GEO-01 (experimental)

`src/temporal-validation.mjs` implementa un evaluador **offline** de país-año mediante rolling-origin, con ventana de test predefinida, embargo de etiquetas, disponibilidad declarada de fuentes y estado previo, comparadores global y condicional, regularización jerárquica por país, métricas Brier/log-loss, calibración descriptiva y alertas con cupo fijo. Sus pruebas adversariales están en `tests/temporal-validation.test.mjs`.

**Este evaluador local no ha emitido predicciones verificadas**: sus pruebas de unidad siguen empleando ejemplos sintéticos; el contraste retrospectivo real entre ediciones se ejecuta mediante el script institucional independiente documentado en el apartado anterior. Las fechas y hashes de entrada no se autentican automáticamente: el resultado permanece etiquetado `RETROSPECTIVE_ROLLING_ORIGIN_ASOF_SELF_REPORTED`. No se publica el código del evaluador en Pages ni se mezclan archivos personales. El contraste real entre UCDP 23.1/25.1 de 2024 continúa siendo no concluyente: Brier peor y log-loss mejor que el baseline, con un solo evento.

## Ejecución

Sitio HTML/CSS/JS sin framework ni dependencias externas. Para previsualizarlo, servir la carpeta mediante un servidor estático (por ejemplo, `python3 -m http.server 8000`) y abrir la raíz del servidor. No abrir `index.html` directamente mediante `file://`, porque la carga del JSON usa `fetch`.

```bash
node --test tests/*.test.mjs
python3 scripts/audit_public.py
```

GitHub Actions ejecuta las pruebas, comprueba los autores, audita el árbol público y publica exclusivamente `index.html`, `styles.css`, `logo.svg`, `favicon.svg`, `src/site.mjs`, `src/metrics.mjs` y `data/demo.json`, así como `src/research.mjs` y `data/research.json`, además de `src/project-catalog.mjs`, `src/project-portfolio.mjs` y `data/projects.json` depurado. Ningún README, workflow, archivo de desarrollo o configuración de repositorio forma parte del paquete desplegado.

## Requisitos para datos reales

Toda observación requiere licencia de redistribución, fuente primaria, fecha de publicación, edición temporal recuperable y protocolo de evaluación. Los pronósticos necesitan fecha de emisión verificable anterior al desenlace y comparación con un baseline. Las evaluaciones retrospectivas no se presentarán como pruebas prospectivas.

El sitio es una demostración pública autocontenida: no incorpora credenciales, endpoints de acceso privado ni datasets experimentales. Se auditan sus activos y dependencias antes de cada publicación.

© IDEA LAB. Derechos reservados salvo indicación expresa.
