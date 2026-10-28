# Especificación

## Problema
La coordinación de un laboratorio registra pedidos en mensajes y una planilla. A veces se confirma la misma unidad para horarios superpuestos y a veces una cancelación sigue bloqueando el horario.

## Alcance
Aplicación local de consola que permite consultar disponibilidad por unidad e intervalo, crear reservas, cancelarlas conservando el historial y persistir todo entre ejecuciones.

## Inventario (fijo, precargado en data/inventario.json)
| ID | Equipo |
|---|---|
| MIC-01 | Microscopio digital |
| MIC-02 | Microscopio digital |
| OSC-01 | Osciloscopio |
| MUL-01 | Multímetro |
| FUE-01 | Fuente de alimentación |

Cada ID es una unidad física distinta.

## Requisitos verificables
- R1: Leer el inventario y consultar disponibilidad de una unidad para un intervalo. La consulta aplica las mismas validaciones que la creación (unidad conocida, fechas válidas, inicio < fin, inicio no pasado).
- R2: Crear una reserva con id, unidad, solicitante, inicio y fin (una unidad por reserva).
- R3: Cancelar una reserva conservando id y datos; el intervalo queda libre.
- R4: Persistir reservas y estados y recuperarlos al reiniciar.
- R5: Validar unidad conocida, solicitante válido, fechas válidas e inicio < fin.
- R6: Rechazar superposiciones de reservas activas de la misma unidad.
- R7: La disponibilidad usa el mismo predicado de superposición y las mismas validaciones que la creación.

## Reglas
- Intervalos semiabiertos [inicio, fin): 10:00-11:00 y 11:00-12:00 no se superponen.
- Solo las reservas activas ocupan el intervalo; las canceladas no bloquean.
- Unidades distintas pueden reservarse a la vez.
- Solicitante: no vacío ni solo espacios.
- Cancelar una reserva ya cancelada es un error. Cancelar un id inexistente es un error.

## Supuestos
- Zona horaria: UTC-3 fija (Argentina no tiene horario de verano).
- Formato de fecha: ISO 8601 con offset -03:00, ej. 2026-11-03T10:00:00-03:00. Sin offset, o con otro offset, se rechaza.
- Fechas pasadas: se rechaza un inicio anterior al momento actual; un inicio igual al momento actual se acepta. Esto aplica a la creación y a la consulta de disponibilidad. El reloj es inyectable en las pruebas.
- Duración: sin mínimo ni máximo, salvo inicio < fin. Sin límite de anticipación.
- El solicitante se guarda sin espacios al inicio ni al final ("  Ana " se guarda como "Ana").
- Los errores de dominio son ValueError con mensaje en español; no distinguen tipo de error.
- Ids de reserva secuenciales y legibles (RES-001, RES-002...), generados al crear y nunca reutilizados.
- Persistencia en data/reservas.json (no versionado), con escritura atómica.
- Un solo usuario local, sin autenticación.

## Fuera de alcance
Autenticación y roles, notificaciones, pagos, integraciones externas, despliegue, interfaz compleja, concurrencia distribuida, escalabilidad, administración del inventario.

## Criterios de aceptación y pruebas
| Criterio | Requisito | Prueba | Estado |
|---|---|---|---|
| Creación válida devuelve reserva activa con id | R2 | test_creacion_valida | ejecutada |
| MIC-01 10:00-11:00 rechaza 10:30-11:30 | R6 | test_rechazo_superposicion | ejecutada |
| MIC-01 10:00-11:00 permite 11:00-12:00 | R6 | test_limites_consecutivos | ejecutada |
| MIC-02 10:00-11:00 permitido con MIC-01 ocupado | R6 | test_mic_02_simultanea | ejecutada |
| Unidad desconocida, solicitante vacío o solo espacios, fecha inválida o inexistente, sin offset, offset distinto, inicio = fin, inicio > fin, inicio pasado: rechazados | R5 | test_entradas_invalidas | ejecutada |
| Cancelar conserva id y datos y libera el horario | R3 | test_cancelacion_conserva_registro_y_libera_horario | ejecutada |
| Cancelar dos veces da error | R3 | test_cancelar_reserva_ya_cancelada_da_error | ejecutada |
| Disponibilidad coincide con lo que permite la creación | R7 | test_disponibilidad_consistente_con_creacion | ejecutada |
| Disponibilidad con inicio pasado da error | R1, R7 | test_disponibilidad_con_inicio_pasado_da_error | ejecutada |
| Inicio igual al momento actual se acepta | R5 | test_inicio_igual_al_momento_actual_se_acepta | ejecutada |
| Reservas activas y canceladas persisten tras reiniciar; los ids continúan la secuencia | R4 | test_persiste_reservas_y_continua_secuencia_tras_reiniciar | ejecutada (automática) |
| Tras reiniciar, una cancelada no bloquea y una activa sí | R4, R7 | test_consulta_tras_reiniciar_respeta_estados | ejecutada (automática) |
| Archivo JSON corrupto da error y no se modifica | R4 | test_archivo_corrupto_da_error_y_no_se_modifica | ejecutada (automática) |
| Persistencia con reinicio real del proceso | R4 | procedimiento manual (etapa 3) | pendiente |

## Historial de cambios de la especificación
- 28/10/2026 (versión inicial): requisitos R1-R7, reglas y supuestos.
- 28/10/2026 (revisión tras etapa 1): se aclara en R1/R7 que la disponibilidad aplica las mismas validaciones que la creación, incluido el inicio no pasado. Motivo: la revisión encontró que la consulta mostraba "disponible" un horario que la creación rechazaba. Se agregan supuestos (strip del solicitante, ValueError, formato de ids) y los nombres reales de las pruebas.
- 28/10/2026 (cierre de etapa 2): se actualiza la tabla con las pruebas reales de persistencia y de inicio igual al momento actual. Se separa la verificación automática de la manual, que sigue pendiente hasta tener la consola.