# PSICOHISTORIA · IDEA LAB

Laboratorio público de investigación de sistemas complejos, fenómenos colectivos y evaluación de pronósticos.

**Estado actual: versión pública experimental, reconstruida de forma independiente.** El sitio incluye diez vistas navegables con formato oscuro, mapa de investigación, explorador de escenarios, evaluación probabilística, registro y hoja de ruta, y herramientas locales de preparación de hipótesis y guiones.

## Navegación

| Grupo | Vistas | Función pública |
| --- | --- | --- |
| Inicio | Resumen | Estado, líneas científicas y siguientes pasos |
| Predicciones | Explorador; Riesgos 2027 | Árbol sintético, supuestos y protocolo de emisión |
| Investigación | Mapa; Líneas y fuentes; Evidencia; Registro; Hitos | Estudios de demostración, Brier score, baselines y trazabilidad |
| Crear | Ideas y sinergias; Estudio audiovisual | Borradores locales y guion de texto |

**Investigación institucional:** siete líneas de preguntas científicas con fuentes primarias, comparadores y condiciones pendientes. El CSV local permite comprobar fórmulas y un orden temporal declarado; la fecha real de publicación no se certifica y no existe evidencia de utilidad predictiva prospectiva.

**Límites de esta versión:** no contiene los históricos reales, catálogos de países, predicciones de cohortes, modelos calibrados con observaciones oficiales ni los componentes de generación audiovisual. Tampoco permite escritura en un backend: las ideas se generan en memoria y pueden exportarse localmente. Ninguna cifra sintética es una previsión real.

## Ejecución

Sitio HTML/CSS/JS sin framework ni dependencias externas. Para previsualizarlo, servir la carpeta mediante un servidor estático (por ejemplo, `python3 -m http.server 8000`) y abrir la raíz del servidor. No abrir `index.html` directamente mediante `file://`, porque la carga del JSON usa `fetch`.

```bash
node --test tests/*.test.mjs
python3 scripts/audit_public.py
```

GitHub Actions ejecuta las pruebas, comprueba los autores, audita el árbol público y publica exclusivamente `index.html`, `styles.css`, `logo.svg`, `favicon.svg`, `src/site.mjs`, `src/metrics.mjs` y `data/demo.json`, así como `src/research.mjs` y `data/research.json`. Ningún README, workflow, archivo de desarrollo o configuración de repositorio forma parte del paquete desplegado.

## Requisitos para datos reales

Toda observación requiere licencia de redistribución, fuente primaria, fecha de publicación, edición temporal recuperable y protocolo de evaluación. Los pronósticos necesitan fecha de emisión verificable anterior al desenlace y comparación con un baseline. Las evaluaciones retrospectivas no se presentarán como pruebas prospectivas.

El sitio es una demostración pública autocontenida: no incorpora credenciales, endpoints de acceso privado ni datasets experimentales. Se auditan sus activos y dependencias antes de cada publicación.

© IDEA LAB. Derechos reservados salvo indicación expresa.
