from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timedelta, timezone
from pathlib import Path

from reservas.dominio import Reserva
from reservas.repositorio import RepositorioReservas


_ZONA_HORARIA = timezone(timedelta(hours=-3))


def _crear_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sistema local de reservas de equipos de laboratorio."
    )
    subcomandos = parser.add_subparsers(dest="comando", required=True)

    subcomandos.add_parser("equipos", help="Mostrar el inventario")

    disponibilidad = subcomandos.add_parser(
        "disponibilidad", help="Consultar disponibilidad de una unidad"
    )
    disponibilidad.add_argument("unidad")
    disponibilidad.add_argument("inicio")
    disponibilidad.add_argument("fin")

    reservar = subcomandos.add_parser("reservar", help="Crear una reserva")
    reservar.add_argument("unidad")
    reservar.add_argument("solicitante")
    reservar.add_argument("inicio")
    reservar.add_argument("fin")

    subcomandos.add_parser("listar", help="Listar todas las reservas")

    cancelar = subcomandos.add_parser("cancelar", help="Cancelar una reserva")
    cancelar.add_argument("id")
    return parser


def _cargar_inventario(ruta: Path) -> Mapping[str, str]:
    try:
        with ruta.open(encoding="utf-8") as archivo:
            inventario = json.load(archivo)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"No se pudo cargar el inventario ({ruta}): {error}") from error
    if not isinstance(inventario, dict) or not all(
        isinstance(unidad, str) and isinstance(nombre, str)
        for unidad, nombre in inventario.items()
    ):
        raise ValueError(f"El inventario tiene un formato inválido: {ruta}")
    return inventario


def _mostrar_reserva(reserva: Reserva) -> None:
    print(
        f"{reserva.id}\t{reserva.unidad}\t{reserva.solicitante}\t"
        f"{reserva.inicio.isoformat()}\t{reserva.fin.isoformat()}\t"
        f"{reserva.estado}"
    )


def main(
    argv: Sequence[str] | None = None,
    *,
    ruta_inventario: str | Path | None = None,
    ruta_reservas: str | Path | None = None,
    reloj: Callable[[], datetime] | None = None,
) -> int:
    argumentos = _crear_parser().parse_args(argv)
    directorio_data = Path(__file__).resolve().parent.parent / "data"
    usar_data_local = ruta_inventario is None or ruta_reservas is None
    if ruta_inventario is None:
        ruta_inventario = directorio_data / "inventario.json"
    if ruta_reservas is None:
        ruta_reservas = directorio_data / "reservas.json"
    ruta_inventario = Path(ruta_inventario)
    ruta_reservas = Path(ruta_reservas)

    try:
        if usar_data_local:
            directorio_data.mkdir(parents=True, exist_ok=True)
        ruta_reservas.parent.mkdir(parents=True, exist_ok=True)
        inventario = _cargar_inventario(ruta_inventario)
        if argumentos.comando == "equipos":
            for unidad, nombre in inventario.items():
                print(f"{unidad}\t{nombre}")
            return 0

        repositorio = RepositorioReservas(
            ruta_reservas,
            inventario=inventario,
            reloj=reloj if reloj is not None else lambda: datetime.now(_ZONA_HORARIA),
        )

        if argumentos.comando == "disponibilidad":
            disponible = repositorio.consultar_disponibilidad(
                argumentos.unidad,
                argumentos.inicio,
                argumentos.fin,
            )
            resultado = "disponible" if disponible else "no disponible"
            print(f"{argumentos.unidad} {resultado}")
        elif argumentos.comando == "reservar":
            reserva = repositorio.crear(
                argumentos.unidad,
                argumentos.solicitante,
                argumentos.inicio,
                argumentos.fin,
            )
            print(f"Reserva creada: {reserva.id}")
        elif argumentos.comando == "listar":
            reservas = repositorio.listar()
            if not reservas:
                print("No hay reservas.")
            else:
                print("id\tunidad\tsolicitante\tinicio\tfin\testado")
                for reserva in reservas:
                    _mostrar_reserva(reserva)
        elif argumentos.comando == "cancelar":
            reserva = repositorio.cancelar(argumentos.id)
            print(f"{reserva.id} {reserva.estado}")
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
