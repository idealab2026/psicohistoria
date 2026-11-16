# GEO2027 — Puerta de resolución oficial 196/196 y evaluación prospectiva sin fuga

**Estado a 16 de noviembre de 2026:** `NOT_READY_NO_VERIFIED_OFFICIAL_2027_RELEASE`. Los resultados de violencia estatal organizada **de 2027 todavía no pueden conocerse**. No se calcula ni se publica un Brier sobre etiquetas inventadas, importadas desde otro período o deducidas de que falte una fila.

## 1. Problema que resuelve

El laboratorio ya tiene tres archivos irrevocables para el mismo año objetivo y el mismo universo institucional de **196 GWNO**: primera emisión GEO (196), primera sombra LOG1P (196) y nueva sombra global-only calibrada por país (196), con brazos α=0/1, además de 15 alertas congeladas. Su evaluación principal registrada es

\[
\Delta Brier=Brier(\mathrm{global\ only\ matched\ }\alpha1)
              -Brier(\mathrm{LOG1P\ original}).
\]

Una comparación prospectiva no es científicamente defendible si se cambia la fecha o el universo, se puntúan solo países seleccionados tras conocer resultados, se usa una edición corregida preferida por conveniencia o se codifican países ausentes como 0. Se exige **la primera edición oficial de UCDP OrganizedViolenceCY con las 196 filas de 2027 observadas**, y se conserva por separado el resto de comparaciones, incluido un control intercept-only.

## 2. Validación técnica de archivo futuro

El programa `scripts/resolve_geo2027_first_complete_official.py` ejecutado **sin argumentos** comprueba los SHA de todos los pronósticos y responde con **`NOT_READY`**, sin métricas. El archivo `data/geo2027-full196-resolution-readiness.json` es la representación reproducible de ese estado, y CI requiere igualdad de bytes.

**Solo en 2028 o después**, con archivo de origen y ficha de procedencia revisada por un operador, se habilita una resolución que:

1. Compara SHA-256 del archivo UCDP recibido con el de la ficha de revisión; acepta CSV oficial o ZIP con un solo CSV. Reconoce las variantes de columnas `country_id,year,sb_total_deaths_best` y `country_id_cy,year_cy,sb_total_deaths_best_cy`.
2. Exige **una fila expresa por cada uno de los 196 GWNO originales en el año 2027**, rechaza duplicidades, conteos en blanco, negativos o decimales; los verdaderos ceros requieren un 0 escrito en la columna. Se permiten otros países o años de la misma fuente, pero el cálculo ignora por completo los posteriores a 2027.
3. Verifica que la edición se declara publicada después de finalizar 2027 y que la fecha de la revisión es posterior a la publicación y anterior al momento de ejecución. No existe un mecanismo que autorice puntuar retrospectivamente el resultado de 2027 durante 2026.
4. Exige una ficha JSON con enlaces oficiales HTTPS para la descarga, página de la edición y archivo histórico de ediciones; requiere que la ficha documente cómo se comprobó que **no hubo edición completa anterior**. Registra SHA de esa ficha, fecha de publicación, de revisión y ediciones anteriores examinadas.
5. **No finge que esa documentación se verifica sola**: la autenticidad de UCDP y que esa edición sea realmente la primera completa requieren **comprobación humana externa**. El programa valida la coherencia formal de la ficha; una ficha fraudulenta podría superar esa comprobación. El resultado se identifica como «operator attested», **no como certificación automática independiente**.
6. Calcula Brier y log-loss para los **cinco brazos ya registrados**, siempre sobre los 196 países y con el denominador 196. Publica todos sus resultados, no solo el mejor. Conserva la diferencia primaria firmada y las siete diferencias registradas previamente en el primer pronóstico global-only.
7. Vuelve a calcular la diferencia primaria país a país y exige coincidencia numérica con la **identidad algebraica documentada antes de observar resultados** en `data/geo2027-global-only-issued-disagreement.json`. No reentrena ningún pronóstico ni ajusta umbrales, coeficientes o universos.

La puntuación futura requiere **ambos argumentos**: `--source <archivo.csv/zip> --provenance <revision.json>`. El programa imprime una evaluación reproducible, pero **no modifica ningún archivo SHA-congelado ni publica automáticamente resultados**. Antes de publicar un resultado el operador debe comprobar externamente URLs, historial de ediciones, fecha y cobertura y conservar la ficha verificable.

## 3. Evidencia y límites

Las pruebas automáticas usan **datos sintéticos etiquetados explícitamente** para comprobar que el cálculo matemático es correcto: 196 filas cero/activo, 24 frente a 25 muertes, ausencia de un solo país, conteos en blanco, duplicados, otros años, ZIP/CSV, fuente SHA incorrecta, fecha de publicación imposible y ausencia de revisión. Una prueba compara el score calculado con la identidad del Brier de las probabilidades congeladas.

**Estas pruebas no son una evaluación de 2027**: ningún archivo sintético se registra como resultado real, ningún test publica un Brier de 2027 y el informe de preparación mantiene 0 observaciones oficiales resueltas. No se presenta un p-valor IID para países geopolíticamente dependientes. Aunque en 2028 hubiera un resultado favorable, la comparación global-only frente a LOG1P será **solo el contraste principal prospectivo acordado**; seleccionar el mejor de cinco brazos después de verlo sería una comparación múltiple exploratoria.

## 4. Integridad y privacidad

Se comprueban SHA-256 del GEO original `5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5`, sombra LOG1P `52686923315854557a796f8f192d376dab77a4e03b14c1aeb6b4091e48104f90`, sombra global-only `251595a12758e006cf21dabbb9771e10b5961c469a5317d6b2b1c5de227f3697` y 15 alertas `309b4f270e1d0d6382b7a90ae64c28d7621f96fbf3177a45aaebbffb0f958acb`. No se añade conexión con repositorios ni cuentas personales. La ficha de revisión futura debe contener datos editoriales institucionales, **no nombres o credenciales personales**.

**Archivo de estado:** `data/geo2027-full196-resolution-readiness.json`. **Programa:** `scripts/resolve_geo2027_first_complete_official.py`. **Tests sintéticos:** `scripts/test_resolve_geo2027_first_complete_official.py`. CI y Pages exigen que el estado NOT_READY permanezca coherente mientras no haya resultados.
