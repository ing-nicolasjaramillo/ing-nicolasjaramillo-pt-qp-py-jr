"""Cálculo de lo que se le cobra a una tarjeta por sus validaciones."""

from datetime import datetime, timedelta, timezone

from app.config import (
    DESCUENTOS,
    MAX_TRANSBORDOS,
    MULTIPLO_REDONDEO,
    PORCENTAJE_BASE,
    TARIFA_BASE,
    VALOR_TRANSBORDO,
    VALOR_TRANSBORDO_GRATIS,
    VENTANA_TRANSBORDO_MIN,
)
from app.modelos import Cobro, Perfil, RespuestaTarifa, SolicitudTarifa


def aplicar_descuento(valor: int, perfil: Perfil) -> int:
    """Aplica el descuento y redondea al múltiplo configurado más cercano."""
    porcentaje_descuento = DESCUENTOS[perfil.value]
    numerador = valor * (PORCENTAJE_BASE - porcentaje_descuento)
    denominador = PORCENTAJE_BASE * MULTIPLO_REDONDEO
    unidades, residuo = divmod(numerador, denominador)
    if residuo >= denominador - residuo:
        unidades += 1
    return unidades * MULTIPLO_REDONDEO


def calcular_tarifa(solicitud: SolicitudTarifa) -> RespuestaTarifa:
    ventana_transbordo = timedelta(minutes=VENTANA_TRANSBORDO_MIN)
    inicio_viaje: datetime | None = None
    transbordos_usados = 0
    cobros: list[Cobro] = []

    validaciones_ordenadas = sorted(
        solicitud.validaciones,
        key=lambda validacion: validacion.fecha_hora.astimezone(timezone.utc),
    )

    for validacion in validaciones_ordenadas:
        instante = validacion.fecha_hora.astimezone(timezone.utc)
        if (
            inicio_viaje is None
            or instante - inicio_viaje > ventana_transbordo
            or transbordos_usados >= MAX_TRANSBORDOS
        ):
            tipo = "tarifa"
            valor = aplicar_descuento(TARIFA_BASE, solicitud.perfil)
            inicio_viaje = instante
            transbordos_usados = 0
        elif transbordos_usados == 0:
            tipo = "transbordo"
            valor = aplicar_descuento(VALOR_TRANSBORDO, solicitud.perfil)
            transbordos_usados += 1
        else:
            tipo = "transbordo_gratis"
            valor = aplicar_descuento(VALOR_TRANSBORDO_GRATIS, solicitud.perfil)
            transbordos_usados += 1

        cobros.append(
            Cobro(
                validacion_id=validacion.id,
                fecha_hora=validacion.fecha_hora,
                tipo=tipo,
                valor=valor,
            )
        )

    total = sum(c.valor for c in cobros)
    return RespuestaTarifa(
        tarjeta=solicitud.tarjeta,
        perfil=solicitud.perfil,
        cobros=cobros,
        total=total,
    )
