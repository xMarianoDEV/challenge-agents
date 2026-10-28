from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timedelta


ESTADO_ACTIVA = "activa"
ESTADO_CANCELADA = "cancelada"
_OFFSET_LOCAL = timedelta(hours=-3)


@dataclass(frozen=True)
class Reserva:
    id: str
    unidad: str
    solicitante: str
    inicio: datetime
    fin: datetime
    estado: str = ESTADO_ACTIVA


def parsear_fecha(valor: str) -> datetime:
    if not isinstance(valor, str):
        raise ValueError("La fecha debe ser una cadena ISO 8601.")
    try:
        fecha = datetime.fromisoformat(valor)
    except ValueError as error:
        raise ValueError("La fecha debe ser ISO 8601 válida con offset UTC-03:00.") from error
    if fecha.utcoffset() != _OFFSET_LOCAL:
        raise ValueError("La fecha debe incluir el offset fijo UTC-03:00.")
    return fecha


def se_superponen(
    inicio_a: datetime,
    fin_a: datetime,
    inicio_b: datetime,
    fin_b: datetime,
) -> bool:
    return inicio_a < fin_b and inicio_b < fin_a


def consultar_disponibilidad(
    reservas: Sequence[Reserva],
    inventario: Mapping[str, str],
    unidad: str,
    inicio: str,
    fin: str,
) -> bool:
    if unidad not in inventario:
        raise ValueError(f"Unidad desconocida: {unidad}")
    inicio_fecha, fin_fecha = _validar_intervalo(inicio, fin)
    return not any(
        reserva.estado == ESTADO_ACTIVA
        and reserva.unidad == unidad
        and se_superponen(inicio_fecha, fin_fecha, reserva.inicio, reserva.fin)
        for reserva in reservas
    )


def crear_reserva(
    reservas: Sequence[Reserva],
    inventario: Mapping[str, str],
    unidad: str,
    solicitante: str,
    inicio: str,
    fin: str,
    *,
    reloj: Callable[[], datetime],
    generar_id: Callable[[], str],
) -> Reserva:
    if unidad not in inventario:
        raise ValueError(f"Unidad desconocida: {unidad}")
    if not isinstance(solicitante, str) or not solicitante.strip():
        raise ValueError("El solicitante no puede estar vacío.")

    inicio_fecha, fin_fecha = _validar_intervalo(inicio, fin)
    ahora = reloj()
    if ahora.tzinfo is None or ahora.utcoffset() is None:
        raise ValueError("El reloj debe devolver una fecha con zona horaria.")
    if inicio_fecha < ahora:
        raise ValueError("No se pueden crear reservas con inicio en el pasado.")
    if not consultar_disponibilidad(
        reservas, inventario, unidad, inicio, fin
    ):
        raise ValueError("La unidad ya está reservada durante ese intervalo.")

    id_reserva = generar_id()
    if not isinstance(id_reserva, str) or not id_reserva.strip():
        raise ValueError("El id de reserva no puede estar vacío.")
    if any(reserva.id == id_reserva for reserva in reservas):
        raise ValueError(f"El id de reserva ya existe: {id_reserva}")

    return Reserva(
        id=id_reserva,
        unidad=unidad,
        solicitante=solicitante.strip(),
        inicio=inicio_fecha,
        fin=fin_fecha,
    )


def cancelar_reserva(
    reservas: Sequence[Reserva],
    id_reserva: str,
) -> tuple[Reserva, ...]:
    for indice, reserva in enumerate(reservas):
        if reserva.id == id_reserva:
            if reserva.estado == ESTADO_CANCELADA:
                raise ValueError(f"La reserva ya está cancelada: {id_reserva}")
            reservas_actualizadas = list(reservas)
            reservas_actualizadas[indice] = replace(
                reserva, estado=ESTADO_CANCELADA
            )
            return tuple(reservas_actualizadas)
    raise ValueError(f"No existe la reserva: {id_reserva}")


def _validar_intervalo(inicio: str, fin: str) -> tuple[datetime, datetime]:
    inicio_fecha = parsear_fecha(inicio)
    fin_fecha = parsear_fecha(fin)
    if inicio_fecha >= fin_fecha:
        raise ValueError("El inicio debe ser anterior al fin.")
    return inicio_fecha, fin_fecha
