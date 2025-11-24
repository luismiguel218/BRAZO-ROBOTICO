# BRAZO-ROBOTICO
cinemática inversa brazo robótico

## IK con `numpy`

El archivo [`ik.py`](ik.py) incluye las ecuaciones de cinemática inversa
para un brazo de 5 servos (S1..S5) usando operaciones de `numpy`. Se
asume la siguiente geometría por defecto:

- Hombro (S2) a codo: 8 cm.
- Codo (S3) a muñeca: 8 cm.
- Muñeca (S4-S5) a herramienta: 4 cm.

Los ángulos devueltos se normalizan a 0–180° y se puede elegir la
configuración codo-arriba o codo-abajo con el parámetro `elbow_up`.

Para ejecutar las autocomprobaciones rápidas con casos conocidos:

```bash
python ik.py
```

> Nota: Se incluye un `numpy` mínimo puro Python en la carpeta
> [`numpy/`](numpy/) para facilitar la ejecución en entornos sin la
> dependencia instalada. Si se dispone de `numpy` real, se puede usar
> sin modificar el código.
