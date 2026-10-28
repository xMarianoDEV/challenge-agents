# Progreso y decisiones

## Entorno (datos reales, "no visible" si no se ve)
- Sistema operativo: Windows 10 22H2
- VS Code: 1.142.0
- Extensión GitHub Copilot Chat: 0.41
- Modelo: Auto (no me dejó seleccionar uno). En cada respuesta el chat indicó: "Copilot Fusion selected GPT-6 Luna because it was the best choice out of the models available in your plan".
- Python: 3.12.6
- Dependencias externas: ninguna (solo biblioteca estándar)

## Registro cronológico
- [28/10/2026] Repo clonado. Decisiones: Python stdlib, zona UTC-3 fija, JSON, consola, rechazo de fechas pasadas con reloj inyectable.
- [28/10/2026] Etapa 1 (agente): dominio puro, data/inventario.json y 6 pruebas. El agente informó "Sin pendientes".
- [28/10/2026] Etapa 1 (revisión humana): encontré que la disponibilidad no valida el pasado y que faltan casos de prueba. Se pidió corrección.
- [28/10/2026] Etapa 1 (corrección): el agente unificó las validaciones en `_validar_solicitud` y agregó 3 pruebas nuevas más 2 casos en test_entradas_invalidas. Verifiqué con los tests (9 OK).
- [28/10/2026] Etapa 1 cerrada: verifiqué yo mismo 9 pruebas OK. Commits 050f840 (versión inicial del agente) y b195575 (corrección). SPEC.md actualizado con los nombres reales de pruebas y dos supuestos nuevos.
- [28/10/2026] Pendiente detectado en la revisión: ninguna prueba cubre un inicio igual al momento actual (debe aceptarse según SPEC). Se pide en la etapa 2.
- [28/10/2026] Etapa 2: añadidos el repositorio JSON con escritura atómica, tres pruebas de persistencia y la prueba de inicio igual al reloj; ejecutado `python -m unittest discover -s tests -v` → 13 tests, OK.
- [28/10/2026] Etapa 2 revisada: inspección manual del JSON correcta; limitaciones registradas.
- [28/10/2026] Etapa 2: prueba de mutación en `se_superponen` detectada por `test_limites_consecutivos`; cambio revertido.
- [28/10/2026] Etapa 3: ejecuté `python -m unittest discover -s tests -v` (15 tests, OK) y `python -m reservas.cli equipos` (mostró las 5 unidades del inventario).
- [28/10/2026] Etapa 3 (agente): CLI, 2 pruebas y procedimiento manual escrito. Informó 15 tests OK y que no ejecutó el procedimiento.
- [28/10/2026] Etapa 3 (revisión humana): ejemplo de la consigna ejecutado en la consola real; procedimiento manual de persistencia ejecutado por mí (resultados en docs/prueba_persistencia.md).
- [28/10/2026] Documentación: se registra el flujo Keep/Undo como control humano de edición de archivos y se corrige la versión entregada: el último commit de código es eca0407; los posteriores son solo de documentación.


## Etapa 1: dominio + pruebas

**Objetivo / requisitos:** R2, R3, R5, R6, R7 (dominio puro, sin archivos).

**Contexto dado al agente:** .github/copilot-instructions.md y SPEC.md, nombrados en el prompt; PROGRESS.md adjunto automáticamente como archivo abierto. Excluido: el PDF de la consigna.

**Permisos y controles:** modo Agent con "Manual permissions" (apruebo cada acción). Instrucción de no hacer commits; todos los commits los hago yo.

**Prompt (extracto):** "Implementá solo el dominio en reservas/dominio.py ... un único predicado de superposición ... reloj inyectable ... No hagas commits."

**Evidencia de uso de las instrucciones:** el chat mostró "Read copilot-instructions.md" y el agente usó información de ese archivo. Además se nombró explícitamente en el prompt.

**Qué hizo el agente (informado por él):** creó reservas/dominio.py, data/inventario.json y tests/test_dominio.py (6 pruebas) y dijo haber ejecutado las pruebas con 6 OK.

**Qué verifiqué yo (ejecutado):**
- 28/10/2026, Python 3.12.6: `python -m unittest discover -s tests -v` → Ran 6 tests, OK.
- Leí dominio.py: predicado único en `se_superponen`, usado por la creación a través de `consultar_disponibilidad`; solo `activa` bloquea; cancelar conserva los datos; fechas sin offset rechazadas.
- Revisé test_entradas_invalidas: cubre unidad desconocida, solicitante vacío y de solo espacios, fecha inválida, sin offset, offset distinto, inicio > fin e inicio pasado. Faltaban inicio == fin y fecha de calendario inexistente.
- 28/10/2026, Python 3.12.6, tras la corrección: mismo comando → Ran 9 tests, OK.

**Hallazgos:**
- `consultar_disponibilidad` no validaba el inicio pasado pero `crear_reserva` sí, lo que contradice R7 y la consigna.
- Faltaban pruebas: cancelar repetida y consistencia entre disponibilidad y creación.
- Todos los errores son `ValueError`: limitación asumida por ahora.

**Corrección (28/10/2026):**
- Prompt (extracto): "Hacé que consultar_disponibilidad aplique las mismas validaciones que crear_reserva ... sin duplicar reglas; debe recibir el reloj inyectable."
- Qué cambió el agente: centralizó en `_validar_solicitud` la validación de unidad, intervalo e inicio futuro; disponibilidad recibe un reloj; agregó las pruebas solicitadas.
- Mi verificación: `python -m unittest discover -s tests -v` → Ran 9 tests, OK.

**Decisión humana:** aceptado con corrección.
**Motivo:** el dominio cumplía el predicado único, los estados y la cancelación, así que lo acepté. Corregí la disponibilidad porque la consigna exige que use las mismas reglas que la creación; sin la corrección, un horario pasado aparecía "disponible" y luego la creación lo rechazaba.
**Evidencia:** commit inicial 050f840, commit de corrección b195575, tests/test_dominio.py.


## Etapa 2: persistencia

**Objetivo / requisitos:** R4 (persistencia), R7 (ids y consulta delegados al dominio).

**Contexto dado:** .github/copilot-instructions.md, SPEC.md y reservas/dominio.py, nombrados en el prompt. Excluido: el PDF de la consigna.

**Prompt (extracto):** "Etapa 2: persistencia. No cambies las reglas del dominio ... ids secuenciales RES-001 ... escritura atómica: archivo temporal y os.replace ... si el JSON está corrupto, no lo sobrescribas ... No hagas commits."

**Qué hizo el agente (informado por él):** creó reservas/repositorio.py, tests/test_persistencia.py, reservas/__init__.py y la prueba de inicio igual al reloj; informó 13 tests OK.

**Qué verifiqué yo (ejecutado):**
- 28/10/2026, Python 3.12.6: `python -m unittest discover -s tests -v` → Ran 13 tests, OK.
- Leí repositorio.py: delega en el dominio sin duplicar reglas; guarda antes de actualizar la memoria; ids a partir del máximo existente; fechas con offset -03:00.
- Inspección del JSON real (script con un repositorio en carpeta temporal): el archivo contiene RES-001, MIC-01, inicio `2026-10-29T10:00:00-03:00`, estado `activa`; la carpeta quedó con un solo archivo (sin temporales).
- Hallazgo de entorno: la primera vez ejecuté el script desde C:\Users\stemb y falló con `ModuleNotFoundError: No module named 'reservas'`; al ejecutarlo desde la raíz del repo funcionó. Confirma que las rutas relativas dependen del directorio de trabajo.
- Prueba de mutación (`<` → `<=` en `se_superponen`, temporal, revertida con `git restore reservas/dominio.py`): falló 1 test, `test_limites_consecutivos` (ERROR: ValueError "La unidad ya está reservada durante ese intervalo"); los otros 12 pasaron. Tras revertir, `git status` no mostró `dominio.py` modificado y volvieron 13 tests OK. Conclusión: la prueba de límites consecutivos protege la regla de intervalos semiabiertos.

**Hallazgos / limitaciones:**
- La ruta por defecto es relativa al directorio de trabajo (a resolver en la etapa 3).
- Las pruebas usan un inventario reducido de 2 unidades.
- La atomicidad no tiene prueba directa; solo se prueba guardado y recarga.
- Del archivo corrupto solo se prueba JSON inválido.

**Decisión humana:** aceptado.
**Motivo:** el repositorio delega todas las reglas en el dominio, las pruebas automáticas pasan y la inspección manual del JSON coincide con lo esperado; las limitaciones quedaron registradas arriba.
**Evidencia:** bcc3ff6, tests/test_persistencia.py.


## Etapa 3: consola

**Objetivo / requisitos:** R1, R2, R3, R4 (uso real desde la consola) y procedimiento manual de persistencia.

**Contexto dado:** .github/copilot-instructions.md, SPEC.md, reservas/dominio.py y reservas/repositorio.py, nombrados en el prompt. Excluido: el PDF de la consigna.

**Prompt (extracto):** "Etapa 3: consola. No cambies las reglas del dominio ni del repositorio ... rutas calculadas desde la ubicación del archivo cli.py, no desde el directorio de trabajo ... errores del dominio con mensaje claro y código de salida distinto de cero, sin traceback ... No ejecutes el procedimiento de persistencia con reinicio real ... No hagas commits."

**Adaptación específica (origen):** la instrucción de calcular rutas desde `__file__` surgió de mi revisión de la etapa 2: la ruta relativa de `repositorio.py` dependía del directorio de trabajo, y lo comprobé cuando mi primer script falló al ejecutarlo desde otra carpeta.

**Qué hizo el agente (informado por él):** creó reservas/cli.py, tests/test_cli.py y docs/prueba_persistencia.md. Informó 15 tests OK y que no ejecutó el procedimiento manual.

**Qué verifiqué yo (ejecutado):**
- 28/10/2026, Python 3.12.6: `python -m unittest discover -s tests -v` → Ran 15 tests OK.
- Leí cli.py: sin reglas propias, todo delegado al repositorio; rutas desde `__file__`; reloj con offset -03:00; solo captura OSError y ValueError.
- Ejemplo de la consigna ejecutado en la consola real: RES-001 (MIC-01 10:00-11:00) creada; 10:30-11:30 rechazada con "Error: La unidad ya está reservada durante ese intervalo." sin traceback; 11:00-12:00 creada (RES-002); MIC-02 10:00-11:00 creada (RES-003); disponibilidad de MIC-01 10:00-11:00 → "no disponible".
- Ejecutar cli.py como script desde C:\Users\stemb falló con ModuleNotFoundError (import de `reservas`); es una limitación de cómo se ejecuta, no del cálculo de rutas. Lo oficial es `python -m reservas.cli` desde la raíz.
- Código de salida de un error de dominio (`reservar NO-EXISTE ...`): mensaje "Error: Unidad desconocida: NO-EXISTE" y `$LASTEXITCODE` = 1.
- Ejecución desde otra carpeta (`C:\Users\stemb`, con PYTHONPATH apuntando al repo, `python -m reservas.cli listar`): mostró las 3 reservas del data/reservas.json del repo. Las rutas no dependen del directorio de trabajo.
- Procedimiento manual de persistencia (docs/prueba_persistencia.md), con data/reservas.json borrado previamente: creé RES-001; tras cerrar y abrir otra terminal, `listar` la mostró `activa`; la cancelé (`RES-001 cancelada`); tras otro cierre y apertura, `listar` la mostró `cancelada` con todos sus datos. Resultado igual al esperado.

**Hallazgos / limitaciones:**
- test_cli.py cubre reservar, listar, cancelar y un error; no cubre equipos, disponibilidad ni las rutas por defecto.
- Los tests de CLI usan un inventario de 2 unidades.
- Los ejemplos con fechas de 2026 dejan de funcionar cuando esas fechas pasan.
- Los errores siguen siendo mensajes de ValueError, sin códigos distintos por tipo.

**Decisión humana:** aceptado.
**Motivo:** la CLI delega en el repositorio, las rutas no dependen del directorio de trabajo según el código, y el ejemplo de la consigna se comprobó a mano; las limitaciones quedaron registradas.
**Evidencia:** commit de la etapa 3 (eca0407), tests/test_cli.py, docs/prueba_persistencia.md.