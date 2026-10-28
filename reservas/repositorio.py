from __future__ import annotations

import json
import os
import re
import tempfile
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

from reservas.dominio import (
    ESTADO_ACTIVA,
    ESTADO_CANCELADA,
    Reserva,
    cancelar_reserva,
    consultar_disponibilidad,
    crear_reserva,
    parsear_fecha,
)


_RUTA_PREDETERMINADA = Path("data") / "reservas.json"
_PATRON_ID = re.compile(r"RES-(\d+)")


class RepositorioReservas:
    def __init__(
        self,
        ruta: str | Path = _RUTA_PREDETERMINADA,
        *,
        inventario: Mapping[str, str],
        reloj: Callable[[], datetime],
    ) -> None:
        self._ruta = Path(ruta)
        self._inventario = inventario
        self._reloj = reloj
        self._reservas = self._cargar()
        self._siguiente_numero = max(
            (
                int(match.group(1))
                for reserva in self._reservas
                if (match := _PATRON_ID.fullmatch(reserva.id))
            ),
            default=0,
        ) + 1

    def listar(self) -> tuple[Reserva, ...]:
        return tuple(self._reservas)

    def crear(
        self,
        unidad: str,
        solicitante: str,
        inicio: str,
        fin: str,
    ) -> Reserva:
        reserva = crear_reserva(
            self._reservas,
            self._inventario,
            unidad,
            solicitante,
            inicio,
            fin,
            reloj=self._reloj,
            generar_id=lambda: f"RES-{self._siguiente_numero:03d}",
        )
        reservas_actualizadas = (*self._reservas, reserva)
        self._guardar(reservas_actualizadas)
        self._reservas = reservas_actualizadas
        self._siguiente_numero += 1
        return reserva

    def cancelar(self, id_reserva: str) -> Reserva:
        reservas_actualizadas = cancelar_reserva(self._reservas, id_reserva)
        self._guardar(reservas_actualizadas)
        self._reservas = reservas_actualizadas
        return next(
            reserva
            for reserva in self._reservas
            if reserva.id == id_reserva
        )

    def consultar_disponibilidad(
        self,
        unidad: str,
        inicio: str,
        fin: str,
    ) -> bool:
        return consultar_disponibilidad(
            self._reservas,
            self._inventario,
            unidad,
            inicio,
            fin,
            reloj=self._reloj,
        )

    def _cargar(self) -> tuple[Reserva, ...]:
        try:
            with self._ruta.open(encoding="utf-8") as archivo:
                datos = json.load(archivo)
        except FileNotFoundError:
            return ()
        except json.JSONDecodeError as error:
            raise ValueError(
                f"El archivo de reservas contiene JSON inválido: {self._ruta}"
            ) from error
        except (OSError, UnicodeDecodeError) as error:
            raise ValueError(
                f"No se pudo leer el archivo de reservas: {self._ruta}"
            ) from error

        if not isinstance(datos, list):
            raise ValueError(
                f"El archivo de reservas debe contener una lista: {self._ruta}"
            )

        reservas: list[Reserva] = []
        ids: set[str] = set()
        for indice, registro in enumerate(datos, start=1):
            reservas.append(self._deserializar(registro, indice, ids))
        return tuple(reservas)

    def _deserializar(
        self,
        registro: Any,
        indice: int,
        ids: set[str],
    ) -> Reserva:
        campos = {"id", "unidad", "solicitante", "inicio", "fin", "estado"}
        if not isinstance(registro, dict) or not campos.issubset(registro):
            raise ValueError(
                f"El registro {indice} del archivo de reservas no tiene "
                f"los campos requeridos: {self._ruta}"
            )

        id_reserva = registro["id"]
        unidad = registro["unidad"]
        solicitante = registro["solicitante"]
        estado = registro["estado"]
        if not all(
            isinstance(valor, str)
            for valor in (id_reserva, unidad, solicitante, estado)
        ):
            raise ValueError(
                f"El registro {indice} del archivo de reservas tiene "
                f"campos inválidos: {self._ruta}"
            )
        if not id_reserva or id_reserva in ids:
            raise ValueError(
                f"El registro {indice} tiene un id vacío o duplicado: "
                f"{self._ruta}"
            )
        if unidad not in self._inventario:
            raise ValueError(
                f"El registro {indice} tiene una unidad desconocida: "
                f"{self._ruta}"
            )
        if estado not in (ESTADO_ACTIVA, ESTADO_CANCELADA):
            raise ValueError(
                f"El registro {indice} tiene un estado inválido: {self._ruta}"
            )
        try:
            inicio = parsear_fecha(registro["inicio"])
            fin = parsear_fecha(registro["fin"])
        except ValueError as error:
            raise ValueError(
                f"El registro {indice} tiene fechas inválidas: {self._ruta}"
            ) from error
        if inicio >= fin:
            raise ValueError(
                f"El registro {indice} tiene un intervalo inválido: {self._ruta}"
            )

        ids.add(id_reserva)
        return Reserva(
            id=id_reserva,
            unidad=unidad,
            solicitante=solicitante,
            inicio=inicio,
            fin=fin,
            estado=estado,
        )

    def _guardar(self, reservas: Sequence[Reserva]) -> None:
        datos = [
            {
                "id": reserva.id,
                "unidad": reserva.unidad,
                "solicitante": reserva.solicitante,
                "inicio": reserva.inicio.isoformat(),
                "fin": reserva.fin.isoformat(),
                "estado": reserva.estado,
            }
            for reserva in reservas
        ]
        temporal: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self._ruta.parent,
                prefix=f".{self._ruta.name}.",
                suffix=".tmp",
                delete=False,
            ) as archivo:
                temporal = archivo.name
                json.dump(datos, archivo, ensure_ascii=False, indent=2)
                archivo.write("\n")
            os.replace(temporal, self._ruta)
        finally:
            if temporal is not None:
                try:
                    os.unlink(temporal)
                except FileNotFoundError:
                    pass
