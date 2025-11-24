"""Herramienta de simulación rápida para el brazo robótico.

Permite enviar un set de ángulos, guardar/cargar trayectorias y
obtener resultados de cinemática inversa (IK) dentro de rango.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, List, Sequence

ANGLE_MIN = -180.0
ANGLE_MAX = 180.0
NUM_JOINTS = 6


def clamp(value: float, min_value: float = ANGLE_MIN, max_value: float = ANGLE_MAX) -> float:
    return max(min_value, min(value, max_value))


def parse_angles(raw_angles: Iterable[str]) -> List[float]:
    angles = [float(value) for value in raw_angles]
    if len(angles) != NUM_JOINTS:
        raise ValueError(f"Se esperaban {NUM_JOINTS} ángulos y se recibieron {len(angles)}")
    for idx, angle in enumerate(angles, start=1):
        if not ANGLE_MIN <= angle <= ANGLE_MAX:
            raise ValueError(
                f"El ángulo {idx}={angle}° está fuera de rango ({ANGLE_MIN}° a {ANGLE_MAX}°)."
            )
    return angles


def send_angles(angles: Sequence[float]) -> str:
    # Simula envío al brazo y devuelve ACK
    formatted = ", ".join(f"{a:.2f}°" for a in angles)
    return f"RECIBIDO -> [{formatted}] | ACK"


def save_trajectory(path: Path, angles: Sequence[Sequence[float]]) -> None:
    payload = {"trayectoria": [list(sequence) for sequence in angles]}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def load_trajectory(path: Path) -> List[List[float]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    trayectoria = data.get("trayectoria")
    if not isinstance(trayectoria, list):
        raise ValueError("El archivo no contiene una trayectoria válida")
    for sequence in trayectoria:
        parse_angles(sequence)
    return [list(sequence) for sequence in trayectoria]


def ik_from_target(target: Sequence[float]) -> List[float]:
    if len(target) != 3:
        raise ValueError("La meta debe ser [x, y, z]")
    x, y, z = target
    # IK simplificada: genera ángulos deterministas y clampa a rango.
    estimates = [x * 10.0, y * 10.0, z * 10.0, 0.5 * (x + y) * 10.0, 0.5 * (y + z) * 10.0, 0.5 * (x + z) * 10.0]
    return [clamp(angle) for angle in estimates]


def handle_send(args: argparse.Namespace) -> None:
    angles = parse_angles(args.angles)
    print(send_angles(angles))


def handle_trajectory(args: argparse.Namespace) -> None:
    path = Path(args.file)
    if args.save:
        payload = parse_angles(args.save)
        save_trajectory(path, [payload])
        print(f"Trayectoria guardada en {path}")
    else:
        trayectoria = load_trajectory(path)
        print(f"Trayectoria cargada desde {path} -> {trayectoria}")


def handle_ik(args: argparse.Namespace) -> None:
    target = [float(value) for value in args.target]
    angles = ik_from_target(target)
    print(f"IK({target}) -> {angles}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Simulador y pruebas rápidas para el brazo robótico")
    subparsers = parser.add_subparsers(dest="command", required=True)

    send_parser = subparsers.add_parser("send", help="Enviar un set fijo de ángulos y recibir ACK")
    send_parser.add_argument("--angles", nargs=NUM_JOINTS, required=True, help="Ángulos en grados (6 valores)")
    send_parser.set_defaults(func=handle_send)

    traj_parser = subparsers.add_parser("trajectory", help="Guardar o cargar trayectorias")
    traj_parser.add_argument("file", help="Ruta del archivo JSON de trayectoria")
    traj_parser_group = traj_parser.add_mutually_exclusive_group(required=True)
    traj_parser_group.add_argument("--save", nargs=NUM_JOINTS, help="Guardar un set de ángulos en el archivo")
    traj_parser_group.add_argument("--load", action="store_true", help="Cargar y validar el archivo de trayectoria")
    traj_parser.set_defaults(func=handle_trajectory)

    ik_parser = subparsers.add_parser("ik", help="Generar ángulos con IK y clamping al rango permitido")
    ik_parser.add_argument("--target", nargs=3, required=True, help="Meta cartesiana x y z (en unidades arbitrarias)")
    ik_parser.set_defaults(func=handle_ik)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
