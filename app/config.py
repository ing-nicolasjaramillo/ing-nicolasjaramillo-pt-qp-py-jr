"""Parámetros tarifarios vigentes de la Línea T2.

Valores en pesos colombianos. Los descuentos están en porcentaje.
"""

TARIFA_BASE = 3200
VALOR_TRANSBORDO = 500
VALOR_TRANSBORDO_GRATIS = 0
VENTANA_TRANSBORDO_MIN = 90
MAX_TRANSBORDOS = 2
MULTIPLO_REDONDEO = 50
PORCENTAJE_BASE = 100

DESCUENTOS = {
    "general": 0,
    "estudiante": 35,
    "adulto_mayor": 55,
}
