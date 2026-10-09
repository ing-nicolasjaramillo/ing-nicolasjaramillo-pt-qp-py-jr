# Contexto del proyecto (lo leen todos los agentes)

Servicio `tarifas-t2` (FastAPI + Pydantic v2, Python >= 3.11).
Prueba_Quipux: Los agentes no diseñan la lógica de negocio; la verifican contra la especificación.


## Fuente única de verdad
- `Bitacora.md`, Tarea 1 (secciones 1.2 a 1.11).
- Si algo no está en la Bitácora, se reporta como "no especificado" y no se inventa.
- Si dos secciones de la Bitácora se contradicen, DETENTE y pregunta cuál vale.

## Reglas para todos los agentes
- Respuestas cortas y estructuradas. Sin explicar lo obvio ni repetir archivos completos.
- Una sola pasada por tarea; nada de iterar por cuenta propia.
- Consultar antes de modificar cualquier archivo (Bitácora 1.10).
- No tocar: `pyproject.toml` (warnings = errores, no se desactiva), `.git/`.
- No modificar el contrato de `POST /tarifas/calcular`.
- Alcance actual: SOLO el feature de transbordos. BUG-17 (historial) y Docker quedan fuera.

## Comandos
- Tests: `pytest -q`

