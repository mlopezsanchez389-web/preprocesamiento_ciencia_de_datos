from __future__ import annotations

from typing import Iterable, Mapping, Any

import pandas as pd


ANCHO = 72


def linea(caracter: str = "=") -> None:
    print(caracter * ANCHO)


def titulo(texto: str) -> None:
    print()
    linea("=")
    print(texto.upper())
    linea("=")


def seccion(texto: str) -> None:
    print()
    print(f"-- {texto} --")


def metrica(nombre: str, valor: Any, detalle: str | None = None) -> None:
    if detalle:
        print(f"{nombre}: {valor} | {detalle}")
    else:
        print(f"{nombre}: {valor}")


def dimensiones(filas_iniciales=None, columnas_iniciales=None, filas_finales=None, columnas_finales=None) -> None:
    seccion("Dimensiones")
    if filas_iniciales is not None:
        metrica("Filas iniciales", filas_iniciales)
    if filas_finales is not None:
        metrica("Filas finales", filas_finales)
    if columnas_iniciales is not None:
        metrica("Columnas iniciales", columnas_iniciales)
    if columnas_finales is not None:
        metrica("Columnas finales", columnas_finales)


def lista(nombre: str, valores: Iterable[Any] | None, max_items: int = 25) -> None:
    valores = list(valores or [])
    metrica(nombre, len(valores))
    if len(valores) == 0:
        print("  Ninguno")
        return
    for valor in valores[:max_items]:
        print(f"  - {valor}")
    if len(valores) > max_items:
        print(f"  ... {len(valores) - max_items} elementos mas")


def tabla(nombre: str, df: pd.DataFrame | None, max_filas: int = 20) -> None:
    seccion(nombre)
    if df is None or df.empty:
        print("Sin registros para mostrar.")
        return
    print(df.head(max_filas).to_string(index=False))
    if len(df) > max_filas:
        print(f"... mostrando {max_filas} de {len(df)} filas")


def resumen_diccionario(nombre: str, datos: Mapping[str, Any]) -> None:
    seccion(nombre)
    if not datos:
        print("Sin elementos.")
        return
    for clave, valor in datos.items():
        print(f"- {clave}: {valor}")
