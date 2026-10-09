"""Cálculo de lo que se le cobra a una tarjeta por sus validaciones."""

from app.config import (
    DESCUENTOS,
    MULTIPLO_REDONDEO,
    PORCENTAJE_BASE,
    TARIFA_BASE,
)
from app.modelos import Cobro, Perfil, RespuestaTarifa, SolicitudTarifa


def aplicar_descuento(valor: int, perfil: Perfil) -> int:
    """Aplica el descuento del perfil y redondea al múltiplo de 50 más cercano."""
    porcentaje_descuento = DESCUENTOS[perfil.value]
    numerador = valor * (PORCENTAJE_BASE - porcentaje_descuento)
    denominador = PORCENTAJE_BASE * MULTIPLO_REDONDEO
    unidades, residuo = divmod(numerador, denominador)
    if residuo >= denominador - residuo:
        unidades += 1
    return unidades * MULTIPLO_REDONDEO


def calcular_tarifa(solicitud: SolicitudTarifa) -> RespuestaTarifa:
    # Por ahora cada validación paga la tarifa completa.
    cobros = []
    for validacion in solicitud.validaciones:
        cobros.append(
            Cobro(
                validacion_id=validacion.id,
                fecha_hora=validacion.fecha_hora,
                tipo="tarifa",
                valor=aplicar_descuento(TARIFA_BASE, solicitud.perfil),
            )
        )

    total = sum(c.valor for c in cobros)
    return RespuestaTarifa(
        tarjeta=solicitud.tarjeta,
        perfil=solicitud.perfil,
        cobros=cobros,
        total=total,
    )
