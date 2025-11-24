"""Compatibilidad mínima de ``numpy`` para el entorno sin dependencias.

La implementación expone sólo las funciones empleadas por ``ik.py`` y
se apoya en ``math``. Si el proyecto se instala con ``numpy`` real, este
módulo local puede eliminarse sin afectar al código.
"""

from __future__ import annotations

import math
from typing import Iterable, Tuple


pi = math.pi
float64 = float


def mod(x: float, y: float) -> float:
    return x % y


def hypot(x: float, y: float) -> float:
    return math.hypot(x, y)


def clip(x: float, min_value: float, max_value: float) -> float:
    return min(max(x, min_value), max_value)


def arctan2(y: float, x: float) -> float:
    return math.atan2(y, x)


def arccos(x: float) -> float:
    return math.acos(x)


def radians(x: float) -> float:
    return math.radians(x)


def degrees(x: float) -> float:
    return math.degrees(x)


def isclose(a: float, b: float, *, atol: float = 1e-8) -> bool:
    return math.isclose(a, b, abs_tol=atol)


class ndarray(tuple):
    """Tupla ligera con atributo ``shape`` similar a numpy."""

    @property
    def shape(self) -> Tuple[int, ...]:
        return (len(self),)


_Array = ndarray


def asarray(seq: Iterable[float], dtype=float) -> ndarray:
    return _Array(dtype(x) for x in seq)


def array(seq: Iterable[float], dtype=float) -> ndarray:
    return asarray(seq, dtype=dtype)
