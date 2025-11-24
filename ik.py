import numpy as np
from dataclasses import dataclass
from typing import Dict, Iterable, Tuple


@dataclass
class ArmGeometry:
    """Dimensiones del brazo en centímetros.

    Se asume un brazo con 5 servos (S1..S5):
    - S1: giro de base alrededor de Z.
    - S2: hombro en el plano vertical.
    - S3: codo en el mismo plano.
    - S4: pitch de muñeca para mantener la orientación del efector.
    - S5: roll de muñeca.

    Las longitudes reflejan la geometría usada en las ecuaciones de IK.
    """

    shoulder_length: float = 8.0
    elbow_length: float = 8.0
    wrist_length: float = 4.0


def normalize_to_servo_range(angle_deg: float) -> float:
    """Pliega cualquier ángulo a 0–180°.

    Los servos de hobby habituales aceptan el rango 0–180°. Este helper
    conserva la simetría del plano del brazo: un valor de 190° se refleja
    a 170°, -10° se pliega a 10°, etc.
    """

    folded = float(np.mod(angle_deg, 360.0))
    if folded > 180.0:
        folded = 360.0 - folded
    return float(np.clip(folded, 0.0, 180.0))


def _planar_offsets(target: np.ndarray, geometry: ArmGeometry) -> Tuple[float, float, float]:
    """Calcula datos geométricos básicos para las ecuaciones de IK."""

    x, y, z = target
    planar_radius = np.hypot(x, y)

    if planar_radius == 0 and z == 0:
        raise ValueError("El objetivo no puede coincidir con el eje de la base (indeterminado).")

    # Usamos directamente la geometría asumida sin retraer la muñeca. Esto traduce
    # el modelo físico (tres eslabones) en las ecuaciones.
    wrist_r = planar_radius
    wrist_z = z

    return planar_radius, wrist_r, wrist_z


def solve_ik(
    target: Iterable[float],
    *,
    geometry: ArmGeometry = ArmGeometry(),
    elbow_up: bool = True,
    wrist_roll: float = 90.0,
    wrist_pitch_hint: float | None = None,
) -> Dict[str, float]:
    """Resuelve la cinemática inversa para S1..S5 usando ``numpy``.

    Args:
        target: coordenadas ``(x, y, z)`` del TCP en cm.
        geometry: longitudes usadas en las ecuaciones.
        elbow_up: ``True`` para configuración codo-arriba, ``False`` para codo-abajo.
        wrist_roll: ángulo de S5 en grados (se normaliza).
        wrist_pitch_hint: opcional, fuerza la S4 a un pitch absoluto (grados).

    Returns:
        Diccionario con las claves ``"S1"`` .. ``"S5"`` en grados 0–180.
    """

    target_vec = np.asarray(tuple(target), dtype=np.float64)
    if target_vec.shape != (3,):
        raise ValueError("El objetivo debe tener forma (3,).")

    planar_radius, wrist_r, wrist_z = _planar_offsets(target_vec, geometry)
    x, y, z = target_vec

    s1_rad = np.arctan2(y, x)

    wrist_distance = np.hypot(wrist_r, wrist_z)
    max_reach = geometry.shoulder_length + geometry.elbow_length
    if wrist_distance > max_reach:
        # Escalamos de forma suave para mantener la dirección aunque el objetivo esté fuera de alcance.
        scale = max_reach / wrist_distance
        wrist_r *= scale
        wrist_z *= scale
        wrist_distance = max_reach

    cos_elbow = (
        geometry.shoulder_length**2
        + geometry.elbow_length**2
        - wrist_distance**2
    ) / (2 * geometry.shoulder_length * geometry.elbow_length)
    cos_elbow = float(np.clip(cos_elbow, -1.0, 1.0))
    elbow_theta = np.arccos(cos_elbow)
    elbow_angle_rad = np.pi - elbow_theta  # 0° = brazo extendido, 180° = flexionado hacia atrás

    cos_shoulder = (
        geometry.shoulder_length**2
        + wrist_distance**2
        - geometry.elbow_length**2
    ) / (2 * geometry.shoulder_length * wrist_distance)
    cos_shoulder = float(np.clip(cos_shoulder, -1.0, 1.0))
    shoulder_offset = np.arccos(cos_shoulder)
    shoulder_base = np.arctan2(wrist_z, wrist_r)
    shoulder_angle_rad = shoulder_base - shoulder_offset if elbow_up else shoulder_base + shoulder_offset

    forearm_pitch = shoulder_angle_rad + elbow_angle_rad
    approach_pitch = np.arctan2(z, planar_radius)
    if wrist_pitch_hint is None:
        wrist_pitch_rad = approach_pitch - forearm_pitch
    else:
        wrist_pitch_rad = np.radians(wrist_pitch_hint) - forearm_pitch

    angles = {
        "S1": normalize_to_servo_range(np.degrees(s1_rad)),
        "S2": normalize_to_servo_range(np.degrees(shoulder_angle_rad)),
        "S3": normalize_to_servo_range(np.degrees(elbow_angle_rad)),
        "S4": normalize_to_servo_range(np.degrees(wrist_pitch_rad)),
        "S5": normalize_to_servo_range(wrist_roll),
    }
    return angles


def _check_case(name: str, target: Tuple[float, float, float], expected: Dict[str, float], **kwargs) -> Tuple[str, bool, Dict[str, float]]:
    """Ejecuta un caso de autocomprobación y devuelve el resultado."""

    solution = solve_ik(target, **kwargs)
    ok = True
    for key, exp in expected.items():
        if not np.isclose(solution[key], exp, atol=1.0):
            ok = False
            break
    return name, ok, solution


def run_quick_checks() -> None:
    """Pruebas rápidas con posiciones conocidas."""

    geometry = ArmGeometry()
    cases = [
        (
            "Extensión horizontal eje X",
            (20.0, 0.0, 0.0),
            {"S1": 0.0, "S2": 0.0, "S3": 0.0, "S4": 0.0, "S5": 90.0},
            dict(geometry=geometry, elbow_up=True),
        ),
        (
            "Extensión horizontal eje Y",
            (0.0, 20.0, 0.0),
            {"S1": 90.0, "S2": 0.0, "S3": 0.0, "S4": 0.0, "S5": 90.0},
            dict(geometry=geometry, elbow_up=True),
        ),
        (
            "Objetivo elevado",
            (10.0, 0.0, 10.0),
            {"S1": 0.0, "S2": 17.1, "S3": 55.8, "S4": 27.9},
            dict(geometry=geometry, elbow_up=True),
        ),
        (
            "Codo abajo",
            (10.0, 0.0, 5.0),
            {"S1": 0.0, "S2": 72.2, "S3": 91.4, "S4": 137.0},
            dict(geometry=geometry, elbow_up=False),
        ),
    ]

    for name, target, expected, kwargs in cases:
        case_name, ok, solution = _check_case(name, target, expected, **kwargs)
        estado = "OK" if ok else "FALLO"
        print(f"[{estado}] {case_name}: {solution}")


if __name__ == "__main__":
    run_quick_checks()
