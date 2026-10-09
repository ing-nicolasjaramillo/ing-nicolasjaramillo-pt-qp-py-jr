---
description: Implementa UN paso del plan 1.9 de la Bitácora (1 = modelos, 2 = redondeo, 3 = asignación de tipos).
agent: build
---
Implementa SOLO el paso $ARGUMENTS del plan de implementación (sección 1.9 de `Bitacora.md`).

1. Lee de la Bitácora únicamente las secciones que ese paso necesita:
   - Paso 1 (modelos): 1.3, 1.4, 1.8.
   - Paso 2 (redondeo): 1.2.
   - Paso 3 (asignación): 1.2, 1.5, 1.6.
2. Antes de editar, muéstrame en máx. 8 líneas: qué archivos tocas, qué cambias y por qué
   (citando la sección de la Bitácora). Espera mi confirmación.
3. Con mi OK, haz el cambio mínimo. Usa las constantes de `app/config.py`; nada de valores fijos.
   No toques archivos fuera de los que listaste.
4. Ejecuta `pytest -q` una vez y reporta: N pasan / N fallan.
5. Propón un mensaje de commit (qué y por qué, en español). NO hagas el commit tú.
