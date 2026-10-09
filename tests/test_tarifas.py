import pytest

from app.config import TARIFA_BASE, VALOR_TRANSBORDO
from app.modelos import Perfil
from app.tarifas import aplicar_descuento


def test_general_no_tiene_descuento():
    assert aplicar_descuento(TARIFA_BASE, Perfil.GENERAL) == TARIFA_BASE


def test_descuento_redondea_a_multiplo_de_50():
    assert aplicar_descuento(TARIFA_BASE, Perfil.ESTUDIANTE) % 50 == 0


def test_descuento_estudiante_transbordo_redondea_mitad_hacia_arriba():
    assert aplicar_descuento(VALOR_TRANSBORDO, Perfil.ESTUDIANTE) == 350


@pytest.mark.parametrize(
    ("valor_base", "valor_esperado"),
    [(TARIFA_BASE, 1450), (VALOR_TRANSBORDO, 250)],
    ids=["tarifa-base", "transbordo"],
)
def test_aplicar_descuento_adulto_mayor_tarifa_y_transbordo(
    valor_base: int,
    valor_esperado: int,
):
    assert aplicar_descuento(valor_base, Perfil.ADULTO_MAYOR) == valor_esperado
