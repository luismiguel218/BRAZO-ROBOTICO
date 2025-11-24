# BRAZO-ROBOTICO

Cinemática inversa y pruebas rápidas del brazo robótico.

## Panel de simulación

El script `panel_simulacion.py` permite validar de forma local el envío de ángulos, la carga/guardado de trayectorias y que la IK produzca valores dentro del rango permitido (±180°).

### Envío de un set fijo de ángulos

```bash
python panel_simulacion.py send --angles 0 45 -30 90 0 0
```

Salida esperada: confirma recepción y ACK del set de 6 articulaciones.

### Guardar y cargar trayectorias

Guardar un set en un archivo JSON de trayectoria:

```bash
python panel_simulacion.py trajectory data/trayectoria.json --save 0 30 60 90 0 0
```

Cargar y validar el archivo, verificando que todos los ángulos están en rango:

```bash
python panel_simulacion.py trajectory data/trayectoria.json --load
```

### IK con clamping al rango permitido

Producir ángulos derivados de una meta cartesiana `[x y z]` y asegurar que permanecen en ±180°:

```bash
python panel_simulacion.py ik --target 5 0.5 -3
```

### Notas

- Cada comando valida automáticamente que se proporcionen exactamente 6 ángulos y que estén en el rango de ±180°.
- Si un valor está fuera de rango o falta algún ángulo, el comando detiene la ejecución con un mensaje explicativo.
