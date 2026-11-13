# Registro público unificado de pronósticos prospectivos 2027

**Fecha de integración: 13 de noviembre de 2026.** El registro es una **proyección derivada** de emisiones ya publicadas y fijadas por SHA-256; no crea predicciones, modelos o resultados nuevos.

## Tres cohortes, 424 pares país-pregunta

| Cohorte | Países | Pregunta específica | Primera emisión pública | Fuente de variables al origen |
|---|---:|---|---|---|
| GEO2027 | 196 | Umbral anual de al menos 25 muertes por violencia organizada de base estatal, 2027 | 2026-11-10T17:23:12Z | UCDP OrganizedViolenceCY 26.1, datos hasta 2025 |
| NEWCONF2027 | 196 | Al menos un episodio nuevo de conflicto intraestatal `newconf=1` en 2027 | 2026-11-11T10:10:21Z | Multiple Onset 25.1 (entrenamiento hasta 2024), ACD 26.1 (actividad de origen 2025) |
| ACD2027 | 32 | Al menos un conflicto intraestatal tipo 3/4 en 2027, **entre los 32 países activos en 2025** | 2026-11-12T22:24:56Z | UCDP/PRIO ACD 26.1, datos hasta 2025 |

**424** no son 424 países diferentes ni observaciones independientes. Un país puede aparecer en tres variables objetivo distintas. Los **15 avisos originales de transición GEO** son una selección de 10 posibles entradas y cinco posibles resoluciones dentro de GEO; no añaden 15 predicciones. El modelo GEO calibrado `shadow` tampoco es una nueva cohorte: es otro vector de probabilidades para exactamente los mismos 196 eventos del GEO original.

## Integridad y procedencia

El script `scripts/build_2027_prospective_registry.py` carga las cinco emisiones originales necesarias y coteja los SHA-256 inmutables de los archivos GEO, NEWCONF, ACD, shadow y alertas, además de los compromisos de sus manifiestos y primeros commits públicos. Cruza los códigos GWNO usando **igualdad exacta de identificador**; el nombre institucional del país procede del archivo GEO original, fijado antes de 2027. Valida todos los denominadores y los 15 códigos alertados sin introducir ningún cero ni ningún resultado observado.

La salida `data/prospective-2027-registry.json` es solo una proyección generada del histórico público verificado. La segunda salida `data/prospective-2027-registry-manifest.json` recoge su SHA-256, número de cohortes/filas, y huellas y commits de los originales; es también un registro derivado, **no** un manifiesto de nueva emisión. El CI recompone los bytes de la vista desde los originales y comprueba que coinciden.

La interfaz web lee el informe y su manifiesto, comprueba el hash SHA-256 del informe en el navegador y valida país, variable, probabilidad, fecha, fuente y estado. Las opciones de filtrado por variable, búsqueda de país, navegación por páginas y modelos secundarios **nunca reentrenan** las probabilidades. La ficha enlaza al primer commit público y a la fuente institucional UCDP.

## Lectura correcta

Todos los 424 pares siguen **pendientes del resultado anual 2027**. El registro no evalúa capacidad predictiva ni es un contador de aciertos. GEO, NEWCONF y ACD representan endpoints diferentes, por lo que **no se debe calcular una Brier combinada de los 424 casos** ni comparar directamente sus prevalencias.

- GEO: umbral de muertes *state-based*, no inicio o finalización de guerras.
- NEWCONF: al menos un episodio nuevo registrado por país en el año objetivo.
- ACD: persistencia de presencia de conflicto intraestatal en un subconjunto originalmente activo.

Los modelos secundarios (GEO shadow, ACD país y actividad previa, NEWCONF baseline) están explícitamente marcados como **comparadores**. El registro conserva el modelo primario de cada emisión y muestra las probabilidades secundarias solo bajo un desplegable. El resultado futuro solo podrá actualizarse mediante los evaluadores oficiales de cada cohorte con fuentes independientes y completas. **No se cambia ninguno de los documentos de primera emisión ni se introduce información de 2027.**

**Privacidad:** solo se usan repositorios y archivos institucionales de IDEA LAB. La auditoría pública comprueba el contenido permitido del repositorio y los recursos estáticos publicados.
