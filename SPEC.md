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
- R1: Leer el inventario y consultar disponibilidad de una unidad para un intervalo.
- R2: Crear una reserva con id, unidad, solicitante, inicio y fin (una unidad por reserva).
- R3: Cancelar una reserva conservando id y datos; el intervalo queda libre.
- R4: Persistir reservas y estados y recuperarlos al reiniciar.
- R5: Validar unidad conocida, solicitante válido, fechas válidas e inicio < fin.
- R6: Rechazar superposiciones de reservas activas de la misma unidad.
- R7: La disponibilidad usa el mismo predicado de superposición que la creación.

## Reglas
- Intervalos semiabiertos [inicio, fin): 10:00-11:00 y 11:00-12:00 no se superponen.
- Solo las reservas activas ocupan el intervalo; las canceladas no bloquean.
- Unidades distintas pueden reservarse a la vez.
- Solicitante: no vacío ni solo espacios.
- Cancelar una reserva ya cancelada es un error.

## Supuestos
- Zona horaria: UTC-3 fija (Argentina no tiene horario de verano).
- Formato de fecha: ISO 8601 con offset, ej. 2026-11-03T10:00:00-03:00. Sin offset se rechaza.
- Fechas pasadas: se rechaza un inicio anterior al momento actual (reloj inyectable en las pruebas).
- Duración: sin mínimo ni máximo, salvo inicio < fin. Sin límite de anticipación.
- Un solo usuario local, sin autenticación.

## Fuera de alcance
Autenticación y roles, notificaciones, pagos, integraciones externas, despliegue, interfaz compleja, concurrencia distribuida, escalabilidad, administración del inventario.

## Criterios de aceptación y pruebas (nombres a confirmar)
| Criterio | Requisito | Prueba |
|---|---|---|
| Creación válida devuelve reserva activa con id | R2 | test_creacion_valida |
| MIC-01 10:00-11:00 rechaza 10:30-11:30 | R6 | test_rechazo_superposicion |
| MIC-01 10:00-11:00 permite 11:00-12:00 | R6 | test_limites_consecutivos |
| MIC-02 10:00-11:00 permitido con MIC-01 ocupado | R6 | test_unidades_distintas |
| Unidad desconocida, solicitante vacío o solo espacios, fecha inválida, inicio >= fin, sin offset, inicio pasado: rechazados | R5 | test_entradas_invalidas |
| Cancelar conserva id y datos y libera el horario | R3 | test_cancelacion_conserva_y_libera |
| Cancelar dos veces da error | R3 | test_cancelar_repetida |
| Disponibilidad coincide con lo que permite la creación | R7 | test_disponibilidad_consistente |
| Reservas activas y canceladas persisten tras reiniciar | R4 | test_persistencia_reinicio + procedimiento manual |