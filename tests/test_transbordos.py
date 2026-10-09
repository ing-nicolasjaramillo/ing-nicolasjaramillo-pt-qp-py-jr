from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modelos import Perfil, SolicitudTarifa, Validacion
from app.tarifas import calcular_tarifa


cliente = TestClient(app)


def _validacion(
    validacion_id: str,
    fecha_hora: datetime | str,
    estacion: str = "E01",
) -> Validacion:
    if isinstance(fecha_hora, str):
        fecha_hora = datetime.fromisoformat(fecha_hora)
    return Validacion(id=validacion_id, estacion=estacion, fecha_hora=fecha_hora)


def _calcular(
    *validaciones: Validacion,
    perfil: Perfil = Perfil.GENERAL,
    tarjeta: str = "T-TEST-TRANSBORDO",
):
    solicitud = SolicitudTarifa(
        tarjeta=tarjeta,
        perfil=perfil,
        validaciones=list(validaciones),
    )
    return calcular_tarifa(solicitud)


def test_sin_validaciones_devuelve_200_sin_cobros_y_total_cero():
    respuesta = cliente.post(
        "/tarifas/calcular",
        json={"tarjeta": "T-SIN-VALIDACIONES", "validaciones": []},
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["cobros"] == []
    assert respuesta.json()["total"] == 0


def test_una_sola_validacion_genera_un_cobro_tarifa():
    respuesta = _calcular(
        _validacion("v1", "2025-03-10T07:12:00-05:00"),
    )

    assert len(respuesta.cobros) == 1
    assert respuesta.cobros[0].tipo == "tarifa"
    assert respuesta.cobros[0].valor == 3200


@pytest.mark.parametrize(
    ("segundos_desde_inicio", "tipo_esperado"),
    [(90 * 60, "transbordo"), (90 * 60 + 1, "tarifa")],
    ids=["90-00", "90-01"],
)
def test_ventana_de_transbordo_incluye_90_minutos_y_excluye_90_01(
    segundos_desde_inicio: int,
    tipo_esperado: str,
):
    inicio = datetime(2025, 3, 10, tzinfo=timezone.utc)
    respuesta = _calcular(
        _validacion("v1", inicio),
        _validacion("v2", inicio + timedelta(seconds=segundos_desde_inicio)),
    )

    assert respuesta.cobros[1].tipo == tipo_esperado


def test_secuencia_0_1_2_horas_aplica_tarifa_transbordo_tarifa():
    inicio = datetime(2025, 3, 10, tzinfo=timezone.utc)
    respuesta = _calcular(
        _validacion("v1", inicio),
        _validacion("v2", inicio + timedelta(hours=1)),
        _validacion("v3", inicio + timedelta(hours=2)),
    )

    assert [cobro.tipo for cobro in respuesta.cobros] == [
        "tarifa",
        "transbordo",
        "tarifa",
    ]


def test_cuatro_validaciones_en_90_minutos_reinician_en_la_cuarta():
    inicio = datetime(2025, 3, 10, tzinfo=timezone.utc)
    respuesta = _calcular(
        *(
            _validacion(f"v{indice + 1}", inicio + timedelta(minutes=15 * indice))
            for indice in range(4)
        )
    )

    assert [cobro.tipo for cobro in respuesta.cobros] == [
        "tarifa",
        "transbordo",
        "transbordo_gratis",
        "tarifa",
    ]


def test_validacion_tras_el_tercer_intento_transborda_desde_el_nuevo_inicio():
    inicio = datetime(2025, 3, 10, tzinfo=timezone.utc)
    respuesta = _calcular(
        *(
            _validacion(f"v{indice + 1}", inicio + timedelta(minutes=15 * indice))
            for indice in range(5)
        )
    )

    assert [cobro.tipo for cobro in respuesta.cobros] == [
        "tarifa",
        "transbordo",
        "transbordo_gratis",
        "tarifa",
        "transbordo",
    ]


def test_validaciones_desordenadas_se_devuelven_cronologicamente():
    inicio = datetime(2025, 3, 10, tzinfo=timezone.utc)
    respuesta = _calcular(
        _validacion("v3", inicio + timedelta(hours=2)),
        _validacion("v1", inicio),
        _validacion("v2", inicio + timedelta(hours=1)),
    )

    assert [cobro.validacion_id for cobro in respuesta.cobros] == ["v1", "v2", "v3"]


def test_zonas_z_y_menos_05_se_comparan_por_instante_real():
    respuesta = _calcular(
        _validacion("v1", "2025-03-10T07:00:00Z"),
        _validacion("v2", "2025-03-10T02:30:00-05:00"),
    )

    assert respuesta.cobros[1].tipo == "transbordo"


def test_viaje_que_cruza_medianoche_conserva_el_transbordo():
    respuesta = _calcular(
        _validacion("v1", "2025-03-10T23:30:00-05:00"),
        _validacion("v2", "2025-03-11T00:30:00-05:00"),
    )

    assert [cobro.tipo for cobro in respuesta.cobros] == ["tarifa", "transbordo"]


def test_fecha_hora_sin_zona_horaria_devuelve_422():
    respuesta = cliente.post(
        "/tarifas/calcular",
        json={
            "tarjeta": "T-SIN-ZONA",
            "validaciones": [
                {"id": "v1", "estacion": "E01", "fecha_hora": "2025-03-10T07:12:00"}
            ],
        },
    )

    assert respuesta.status_code == 422


def test_id_repetido_devuelve_422():
    respuesta = cliente.post(
        "/tarifas/calcular",
        json={
            "tarjeta": "T-ID-REPETIDO",
            "validaciones": [
                {"id": "v1", "estacion": "E01", "fecha_hora": "2025-03-10T07:12:00Z"},
                {"id": "v1", "estacion": "E02", "fecha_hora": "2025-03-10T07:20:00Z"},
            ],
        },
    )

    assert respuesta.status_code == 422


@pytest.mark.parametrize("perfil", ["invalido", "GENERAL"], ids=["invalido", "mayuscula"])
def test_perfil_invalido_o_mayuscula_devuelve_422(perfil: str):
    respuesta = cliente.post(
        "/tarifas/calcular",
        json={
            "tarjeta": "T-PERFIL-INVALIDO",
            "perfil": perfil,
            "validaciones": [],
        },
    )

    assert respuesta.status_code == 422


def test_perfil_ausente_se_asume_general():
    respuesta = cliente.post(
        "/tarifas/calcular",
        json={
            "tarjeta": "T-PERFIL-AUSENTE",
            "validaciones": [
                {"id": "v1", "estacion": "E01", "fecha_hora": "2025-03-10T07:12:00Z"}
            ],
        },
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["perfil"] == "general"


def test_redondeo_en_mitad_exacta_sube():
    inicio = datetime(2025, 3, 10, tzinfo=timezone.utc)
    respuesta = _calcular(
        _validacion("v1", inicio),
        _validacion("v2", inicio + timedelta(minutes=15)),
        perfil=Perfil.ESTUDIANTE,
    )

    assert respuesta.cobros[1].valor == 350


def test_transbordo_gratis_con_descuento_cuesta_cero():
    inicio = datetime(2025, 3, 10, tzinfo=timezone.utc)
    respuesta = _calcular(
        *(
            _validacion(f"v{indice + 1}", inicio + timedelta(minutes=15 * indice))
            for indice in range(3)
        ),
        perfil=Perfil.ESTUDIANTE,
    )

    assert respuesta.cobros[2].tipo == "transbordo_gratis"
    assert respuesta.cobros[2].valor == 0


def test_misma_estacion_dentro_de_ventana_cuenta_como_transbordo():
    inicio = datetime(2025, 3, 10, tzinfo=timezone.utc)
    respuesta = _calcular(
        _validacion("v1", inicio, estacion="E01"),
        _validacion("v2", inicio + timedelta(minutes=15), estacion="E01"),
    )

    assert respuesta.cobros[1].tipo == "transbordo"


def test_mismo_instante_con_id_distinto_devuelve_422():
    respuesta = cliente.post(
        "/tarifas/calcular",
        json={
            "tarjeta": "T-MISMO-INSTANTE",
            "validaciones": [
                {"id": "v1", "estacion": "E01", "fecha_hora": "2025-03-10T11:58:27Z"},
                {
                    "id": "v2",
                    "estacion": "E02",
                    "fecha_hora": "2025-03-10T06:58:27-05:00",
                },
            ],
        },
    )

    assert respuesta.status_code == 422


def test_ejemplo_oficial_t_004417_total_3700():
    respuesta = cliente.post(
        "/tarifas/calcular",
        json={
            "tarjeta": "T-004417",
            "perfil": "general",
            "validaciones": [
                {
                    "id": "a1f0",
                    "estacion": "E01",
                    "fecha_hora": "2025-03-10T06:52:10-05:00",
                },
                {
                    "id": "a1f1",
                    "estacion": "E07",
                    "fecha_hora": "2025-03-10T07:31:44-05:00",
                },
            ],
        },
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert [cobro["tipo"] for cobro in cuerpo["cobros"]] == ["tarifa", "transbordo"]
    assert [cobro["valor"] for cobro in cuerpo["cobros"]] == [3200, 500]
    assert cuerpo["total"] == 3700
    assert [cobro["fecha_hora"] for cobro in cuerpo["cobros"]] == [
        "2025-03-10T06:52:10-05:00",
        "2025-03-10T07:31:44-05:00",
    ]
