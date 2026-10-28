# Sistema de reservas de laboratorio

## 1. Especificación breve

Aplicación local de consola para consultar disponibilidad, crear y cancelar
reservas de equipos de laboratorio, conservando el historial y los datos entre
ejecuciones. El inventario es fijo; solo las reservas activas ocupan un horario.
Las fechas usan ISO 8601 con offset UTC-03:00 y no se permiten inicios pasados.

La especificación completa está en [SPEC.md](./SPEC.md), incluido su
[historial de cambios](./SPEC.md#historial-de-cambios-de-la-especificación).
La especificación inicial quedó versionada en el commit `a4b394f`, antes de
escribir código; los cambios posteriores están en el historial de `SPEC.md` y en
el commit `a17c4c7`.

Requisitos:

- **R1:** Leer el inventario y consultar disponibilidad de una unidad para un
  intervalo. La consulta aplica las mismas validaciones que la creación (unidad
  conocida, fechas válidas, inicio < fin, inicio no pasado).
- **R2:** Crear una reserva con id, unidad, solicitante, inicio y fin (una unidad
  por reserva).
- **R3:** Cancelar una reserva conservando id y datos; el intervalo queda libre.
- **R4:** Persistir reservas y estados y recuperarlos al reiniciar.
- **R5:** Validar unidad conocida, solicitante válido, fechas válidas e inicio <
  fin.
- **R6:** Rechazar superposiciones de reservas activas de la misma unidad.
- **R7:** La disponibilidad usa el mismo predicado de superposición y las mismas
  validaciones que la creación.

## 2. Solución

### Estructura

```text
challenge-agents/
├── .github/
│   └── copilot-instructions.md
├── data/
│   ├── inventario.json
│   └── reservas.json        (se crea al usar la app; no versionado)
├── docs/
│   └── prueba_persistencia.md
├── reservas/
│   ├── __init__.py
│   ├── cli.py
│   ├── dominio.py
│   └── repositorio.py
├── tests/
│   ├── test_cli.py
│   ├── test_dominio.py
│   └── test_persistencia.py
├── .gitignore
├── PROGRESS.md
├── README.md
└── SPEC.md
```

### Decisiones y requisitos

- Requisito previo registrado: Python 3.12.6. Dependencias externas: ninguna;
  se usa solo la biblioteca estándar. No hay `requirements.txt` ni archivo de
  bloqueo porque no hay dependencias externas.
- El inventario inicial de unidades físicas está en
  [`data/inventario.json`](./data/inventario.json) y la CLI lo carga desde la
  carpeta `data` junto a los módulos del proyecto.
- Carga inicial: el inventario se lee de `data/inventario.json`;
  `data/reservas.json` se crea solo al guardar la primera reserva.
- El dominio contiene las reglas de validación y superposición. El repositorio
  delega las reglas en el dominio y persiste el JSON con escritura atómica.
- Los datos de reservas se guardan en `data/reservas.json`.
  **Borrar este archivo elimina todas las reservas y su historial persistido.**
- Reinicio de datos: no existe un comando para eso. Para partir de cero hay que
  borrar `data/reservas.json` con la aplicación detenida; esto elimina todas las
  reservas y su historial.
- Para utilizar la aplicación, ejecutar desde la raíz del repositorio:

  ```text
  python -m reservas.cli equipos
  python -m reservas.cli disponibilidad MIC-01 2099-11-03T10:00:00-03:00 2099-11-03T11:00:00-03:00
  python -m reservas.cli reservar MIC-01 "Ana Prueba" 2099-11-03T10:00:00-03:00 2099-11-03T11:00:00-03:00
  python -m reservas.cli listar
  python -m reservas.cli cancelar RES-001
  ```

  Los ejemplos de fechas usan 2099 para que no venzan pronto. Si el solicitante
  incluye espacios, debe ir entre comillas.
- Para ejecutar las pruebas:

  ```text
  python -m unittest discover -s tests -v
  ```

### Supuestos y reglas

- Zona horaria UTC-3 fija (Argentina no tiene horario de verano).
- Fechas ISO 8601 con offset `-03:00`; sin offset o con otro offset se rechazan.
- Se rechaza un inicio anterior al momento actual; un inicio igual al actual se
  acepta. Aplica a creación y disponibilidad.
- Duración sin mínimo ni máximo, salvo `inicio < fin`; sin límite de
  anticipación.
- El solicitante se guarda sin espacios al inicio ni al final (`strip`).
- IDs secuenciales `RES-001`, `RES-002`... y no reutilizados.
- Intervalos semiabiertos `[inicio, fin)`: 10:00-11:00 y 11:00-12:00 no se
  superponen.

### Sesión ejecutada en consola el 28/10/2026

```text
$ python -m reservas.cli reservar MIC-01 "Ana Prueba" 2026-11-03T10:00:00-03:00 2026-11-03T11:00:00-03:00
Reserva creada: RES-001
$ python -m reservas.cli reservar MIC-01 "Luis Prueba" 2026-11-03T10:30:00-03:00 2026-11-03T11:30:00-03:00
Error: La unidad ya está reservada durante ese intervalo.
$ python -m reservas.cli reservar MIC-01 "Luis Prueba" 2026-11-03T11:00:00-03:00 2026-11-03T12:00:00-03:00
Reserva creada: RES-002
$ python -m reservas.cli reservar MIC-02 "Mara Prueba" 2026-11-03T10:00:00-03:00 2026-11-03T11:00:00-03:00
Reserva creada: RES-003
$ python -m reservas.cli disponibilidad MIC-01 2026-11-03T10:00:00-03:00 2026-11-03T11:00:00-03:00
MIC-01 no disponible
$ python -m reservas.cli listar
id	unidad	solicitante	inicio	fin	estado
RES-001	MIC-01	Ana Prueba	2026-11-03T10:00:00-03:00	2026-11-03T11:00:00-03:00	activa
RES-002	MIC-01	Luis Prueba	2026-11-03T11:00:00-03:00	2026-11-03T12:00:00-03:00	activa
RES-003	MIC-02	Mara Prueba	2026-11-03T10:00:00-03:00	2026-11-03T11:00:00-03:00	activa
```

La sesión se ejecutó el 28/10/2026; sus fechas de 2026 vencen. Para repetirla
hay que usar fechas futuras con offset `-03:00`. La salida de `listar` separa
las columnas con tabuladores. También se verificó el código de salida: un error
de dominio devolvió `1` (registrado en [PROGRESS.md](./PROGRESS.md)).

### Limitaciones y pendientes registrados

- Etapa 2: las pruebas no verifican directamente la atomicidad; del archivo
  corrupto solo se prueba JSON inválido. Las pruebas usan un inventario reducido
  de dos unidades.
- La persistencia automática se prueba creando un repositorio nuevo sobre el
  mismo archivo, no con un reinicio real del proceso. El reinicio real se
  verificó solo con el procedimiento manual de
  [`docs/prueba_persistencia.md`](./docs/prueba_persistencia.md): dos reinicios
  de terminal, uno con la reserva activa y otro con la cancelada.
- Etapa 3: `test_cli.py` no cubre `equipos`, `disponibilidad` ni las rutas por
  defecto; sus pruebas usan un inventario de dos unidades. Los ejemplos con
  fechas de 2026 dejan de funcionar cuando esas fechas pasan. Los errores siguen
  siendo mensajes de `ValueError`, sin códigos distintos por tipo.
- La ejecución directa como `python reservas/cli.py` desde otra carpeta produjo
  `ModuleNotFoundError`; la forma documentada es `python -m reservas.cli` desde
  la raíz. El motivo registrado es cómo se ejecuta, no el cálculo de rutas.
- La tabla de criterios de [SPEC.md](./SPEC.md) registra el procedimiento de
  persistencia con reinicio real como ejecutado manualmente; los resultados
  observados están en [`docs/prueba_persistencia.md`](./docs/prueba_persistencia.md).

### Cómo se verificó

**Automático (ejecutado por mí):**

- `python -m unittest discover -s tests -v`: 15 tests, Python 3.12.6.

**Manual (ejecutado por mí):**

- Ejemplo de la consigna en la consola.
- Código de salida `1` ante un error de dominio.
- Ejecución desde otra carpeta con `PYTHONPATH` apuntando al repo; `listar`
  mostró las reservas de `data/reservas.json` del repo.
- Procedimiento [`docs/prueba_persistencia.md`](./docs/prueba_persistencia.md):
  dos reinicios de terminal; la reserva sobrevivió primero activa y luego
  cancelada.
- Inspección del JSON generado con un repositorio en una carpeta temporal.
- Prueba de mutación en `se_superponen`: cambiar `<` por `<=` hizo fallar
  `test_limites_consecutivos`; tras revertir el cambio volvieron a pasar los
  13 tests.

**Informado por el agente y no verificado por mí de forma independiente:**

- PROGRESS.md no marca verificaciones informadas por el agente que no hayan
  sido verificadas por mí de forma independiente.

[Procedimiento manual de persistencia](./docs/prueba_persistencia.md) ·
[Criterios de aceptación y pruebas](./SPEC.md#criterios-de-aceptación-y-pruebas)

## 3. Preparación del agente

### Entorno registrado

Según [PROGRESS.md](./PROGRESS.md):

- Sistema operativo: Windows 10 22H2.
- VS Code: 1.142.0.
- Extensión GitHub Copilot Chat: 0.41.
- Modelo: Auto (no me dejó seleccionar uno). En cada respuesta el chat indicó:
  "Copilot Fusion selected GPT-6 Luna because it was the best choice out of the
  models available in your plan".
- Python: 3.12.6.
- Dependencias externas: ninguna (solo biblioteca estándar).

### Instrucciones, contexto y retención

Las instrucciones del proyecto están en
[.github/copilot-instructions.md](./.github/copilot-instructions.md): establecen
Python estándar, pruebas con `unittest`, ejecución de la suite completa al
terminar, no hacer commits ni push, registrar el progreso y mantener el dominio
puro con reloj inyectable.

En la etapa 1 se nombraron `.github/copilot-instructions.md` y `SPEC.md` en el
prompt; [PROGRESS.md](./PROGRESS.md) se adjuntó como archivo abierto y se excluyó
el PDF de la consigna. En las etapas 2 y 3 se nombraron las instrucciones, la
especificación y los módulos previos pertinentes; el PDF también quedó excluido.
Los contextos e instrucciones concretos de cada etapa se registran en la
sección 4.

El modo y permiso registrados para la etapa 1 fueron Agent con "Manual
permissions" (aprobación de cada acción). También se registró que el humano hace
los commits. Para las etapas posteriores, el permiso específico no está
registrado.

La adaptación específica a las reglas de dominio se documentó en
[.github/copilot-instructions.md](./.github/copilot-instructions.md): intervalos
semiabiertos, un único predicado de superposición, reservas activas como únicas
bloqueantes, cancelación que conserva el registro, offset UTC-03:00 e inicio no
pasado con reloj inyectable. El origen y la evidencia están registrados en
[PROGRESS.md](./PROGRESS.md), incluyendo la corrección solicitada tras detectar
que disponibilidad no validaba el pasado. La regla de intervalos semiabiertos
está en `.github/copilot-instructions.md`; `test_limites_consecutivos` la
verifica y la prueba de mutación (`<` por `<=`) la hizo fallar.

[PROGRESS.md](./PROGRESS.md) se usa como retención del progreso, contexto,
hallazgos, decisiones humanas y comandos ejecutados por etapa.

### Herramientas y controles

- Modo: Agent.
- Permisos para leer y editar archivos del proyecto y ejecutar comandos en la
  terminal: no registrado.
- "Manual permissions" en la etapa 1.
- Los commits los hace el humano.
- Antes de aceptar cada etapa se revisó el código, se corrieron las pruebas y
  se anotó el resultado en PROGRESS.md.

### Función y motivo de la elección

**Función:** GitHub Copilot en modo Agent dentro de VS Code escribió el código y las pruebas por etapas, y ejecutó comandos en la terminal. Yo definí la especificación, revisé cada entrega, corrí las pruebas por mi cuenta e hice todos los commits.

**Motivo:** ya usaba GitHub Copilot en VS Code, así que me resultó más simple trabajar con ese entorno que configurar otro cliente de agente (por ejemplo OpenCode o Codex). Elegí Python con solo la biblioteca estándar porque permite empezar sin instalar dependencias y es reproducible en cualquier máquina con Python; es mi primera vez usando Python y no tenía experiencia previa con el lenguaje.

## 4. Registro de decisiones y delegación

Versión entregada: rama `main`, commit `26972f0` (último commit de código y documentación; el commit siguiente solo registra este hash).

### Decisiones significativas

| Decisión | Motivo | Alternativa descartada | Consecuencia |
|---|---|---|---|
| Python solo con biblioteca estándar | Menos dependencias y ejecución reproducible sin instalar nada | TypeScript/Node con React | Sin interfaz gráfica; solo consola |
| UTC-3 fijo | Argentina no tiene horario de verano; evita depender de tzdata en Windows | Zonas IANA con `zoneinfo` | Si cambiara la regla horaria habría que modificar el código |
| Rechazar inicios pasados con reloj inyectable | Evita reservas sin sentido y permite pruebas con fecha fija | Permitir fechas pasadas | Los ejemplos con fechas fijas vencen con el tiempo |
| Persistencia en JSON con escritura atómica | Sin dependencias y fácil de explicar | SQLite | No hay consultas ni control de concurrencia |
| Consola como interfaz | La consigna no exige interfaz gráfica | API local o interfaz web | Uso solo desde terminal |
| Disponibilidad aplica las mismas validaciones que la creación | Exigido por la consigna y por R7 | Validar solo superposición | Surgió de la revisión de la etapa 1 (ver episodio 1) |

### Etapa 1: corrección de la disponibilidad

- **Objetivo:** completar la validación compartida entre disponibilidad y
  creación, incluyendo unidad, intervalo e inicio no pasado, sin duplicar
  reglas; agregar pruebas de cancelación repetida, consistencia y entradas
  inválidas.
- **Contexto e instrucción:** se nombraron las instrucciones del proyecto y
  `SPEC.md`; el progreso estaba adjunto y el PDF de la consigna fue excluido.
  El extracto registrado pide que `consultar_disponibilidad` aplique las mismas
  validaciones que `crear_reserva` y reciba un reloj inyectable.
- **Acción del agente:** centralizó esas validaciones en `_validar_solicitud`,
  hizo que disponibilidad reciba el reloj y agregó las pruebas solicitadas.
- **Decisión humana y motivo:** aceptado con corrección. El dominio cumplía el
  predicado único, los estados y la cancelación; se corrigió disponibilidad
  porque un horario pasado aparecía disponible y luego creación lo rechazaba.
- **Evidencia:** commits [050f840](https://github.com/xMarianoDEV/challenge-agents/commit/050f840)
  y [b195575](https://github.com/xMarianoDEV/challenge-agents/commit/b195575);
  pruebas en [`tests/test_dominio.py`](./tests/test_dominio.py).

### Etapa 2: persistencia y prueba de mutación

- **Objetivo:** implementar persistencia, secuencia de IDs y consulta delegadas
  al dominio; probar reinicio, cancelación conservada, disponibilidad y JSON
  corrupto.
- **Contexto e instrucción:** se nombraron las instrucciones, `SPEC.md` y
  `reservas/dominio.py`; se excluyó el PDF. La instrucción registrada fue no
  cambiar las reglas del dominio, usar IDs secuenciales, escritura temporal con
  `os.replace` y no sobrescribir silenciosamente un JSON corrupto.
- **Acción del agente:** creó `reservas/repositorio.py`,
  `tests/test_persistencia.py`, `reservas/__init__.py` y la prueba de inicio
  igual al reloj.
- **Decisión humana y motivo:** aceptado. El repositorio delega las reglas en
  el dominio, las pruebas automáticas pasan y la inspección manual del JSON
  coincide con lo esperado.
- **Prueba de mutación registrada:** se cambió temporalmente `<` por `<=` en
  `se_superponen`, se revirtió con `git restore reservas/dominio.py` y falló
  `test_limites_consecutivos`; los otros 12 tests pasaron. Tras revertir,
  volvieron a pasar los 13 tests.
- **Evidencia:** commit [bcc3ff6](https://github.com/xMarianoDEV/challenge-agents/commit/bcc3ff6)
  y [`tests/test_persistencia.py`](./tests/test_persistencia.py).

### Etapa 3: rutas desde `__file__`

- **Objetivo:** implementar la CLI y un procedimiento manual de persistencia,
  sin cambiar las reglas del dominio ni del repositorio.
- **Contexto e instrucción:** se nombraron las instrucciones, `SPEC.md`,
  `reservas/dominio.py` y `reservas/repositorio.py`; se excluyó el PDF. Se
  solicitó calcular las rutas desde la ubicación de `cli.py`, usar hora real
  UTC-03:00, informar errores sin traceback y no ejecutar el procedimiento
  manual con reinicio real.
- **Acción del agente:** creó `reservas/cli.py`, `tests/test_cli.py` y
  `docs/prueba_persistencia.md`; informó 15 tests OK y que no ejecutó el
  procedimiento manual.
- **Decisión humana y motivo:** aceptado. El progreso registra que la CLI delega
  en el repositorio, que las rutas no dependen del directorio de trabajo y que
  el ejemplo de la consigna se comprobó a mano; las limitaciones quedaron
  registradas.
- **Comprobación de rutas:** se ejecutó
  `python -m reservas.cli listar` desde otra carpeta, con `PYTHONPATH` apuntando
  al repo, y mostró las reservas de `data/` del repo.
- **Evidencia:** commit [eca0407](https://github.com/xMarianoDEV/challenge-agents/commit/eca0407),
  [`tests/test_cli.py`](./tests/test_cli.py) y
  [`docs/prueba_persistencia.md`](./docs/prueba_persistencia.md). La revisión
  humana registró que `python reservas/cli.py` ejecutado desde otra carpeta
  produjo `ModuleNotFoundError`; la forma oficial es
  `python -m reservas.cli` desde la raíz.
