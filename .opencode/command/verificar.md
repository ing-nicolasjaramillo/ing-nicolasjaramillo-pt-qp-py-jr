---
description: Corre una sola ronda de verificación (tests + revisión de reglas) sobre el feature.
agent: build
---
Ejecuta UNA ronda, sin reintentos:
1. Invoca @tester sobre: $ARGUMENTS (si viene vacío, todas las reglas de Bitacora.md).
2. Invoca @revisor sobre el diff actual.
3. Devuélveme ambos reportes tal cual, uno debajo del otro. No corrijas nada:
   yo decido qué se cambia.
