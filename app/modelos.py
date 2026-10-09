from datetime import datetime, timezone
from enum import Enum
from typing import Literal, Self

from pydantic import BaseModel, field_validator, model_validator


class Perfil(str, Enum):
    GENERAL = "general"
    ESTUDIANTE = "estudiante"
    ADULTO_MAYOR = "adulto_mayor"


class Validacion(BaseModel):
    id: str
    estacion: str
    fecha_hora: datetime

    @field_validator("fecha_hora")
    @classmethod
    def exigir_zona_horaria(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("fecha_hora debe incluir zona horaria")
        return value


class SolicitudTarifa(BaseModel):
    tarjeta: str
    perfil: Perfil = Perfil.GENERAL
    validaciones: list[Validacion]

    @model_validator(mode="after")
    def validar_validaciones(self) -> Self:
        ids: set[str] = set()
        instantes: set[datetime] = set()

        for validacion in self.validaciones:
            if validacion.id in ids:
                raise ValueError("No puede haber dos validaciones con el mismo id")
            ids.add(validacion.id)

            instante = validacion.fecha_hora.astimezone(timezone.utc)
            if instante in instantes:
                raise ValueError("No puede haber dos validaciones en el mismo instante")
            instantes.add(instante)

        return self


class Cobro(BaseModel):
    validacion_id: str
    fecha_hora: datetime
    tipo: Literal["tarifa", "transbordo", "transbordo_gratis"]
    valor: int


class RespuestaTarifa(BaseModel):
    tarjeta: str
    perfil: Perfil
    cobros: list[Cobro]
    total: int
