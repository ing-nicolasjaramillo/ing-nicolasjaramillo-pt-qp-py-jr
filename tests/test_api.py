from fastapi.testclient import TestClient

from app.config import TARIFA_BASE
from app.main import app

cliente = TestClient(app)


def test_salud():
    r = cliente.get("/salud")
    assert r.status_code == 200
    assert r.json() == {"estado": "ok"}


def test_una_validacion_paga_tarifa_completa():
    r = cliente.post(
        "/tarifas/calcular",
        json={
            "tarjeta": "T-TEST-001",
            "perfil": "general",
            "validaciones": [
                {"id": "v1", "estacion": "E01", "fecha_hora": "2025-03-10T07:12:00-05:00"}
            ],
        },
    )
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["total"] == TARIFA_BASE
    assert cuerpo["cobros"][0]["tipo"] == "tarifa"


def test_historial_registra_el_calculo():
    cliente.post(
        "/tarifas/calcular",
        json={
            "tarjeta": "T-TEST-002",
            "validaciones": [
                {"id": "v1", "estacion": "E04", "fecha_hora": "2025-03-10T09:00:00-05:00"}
            ],
        },
    )
    r = cliente.get("/tarjetas/T-TEST-002/historial")
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_historial_aisla_calculos_por_tarjeta():
    tarjeta_a = "T-BUG-17-A"
    tarjeta_b = "T-BUG-17-B"

    calculo_a = cliente.post(
        "/tarifas/calcular",
        json={
            "tarjeta": tarjeta_a,
            "validaciones": [
                {"id": "bug17-a-v1", "estacion": "E01", "fecha_hora": "2025-03-10T10:00:00-05:00"}
            ],
        },
    )
    assert calculo_a.status_code == 200

    calculo_b = cliente.post(
        "/tarifas/calcular",
        json={
            "tarjeta": tarjeta_b,
            "validaciones": [
                {"id": "bug17-b-v1", "estacion": "E02", "fecha_hora": "2025-03-10T11:00:00-05:00"}
            ],
        },
    )
    assert calculo_b.status_code == 200

    respuesta_a = calculo_a.json()
    respuesta_b = calculo_b.json()
    historial_a = cliente.get(f"/tarjetas/{tarjeta_a}/historial")
    historial_b = cliente.get(f"/tarjetas/{tarjeta_b}/historial")

    assert historial_a.status_code == 200
    assert historial_b.status_code == 200
    assert historial_a.json() == [respuesta_a]
    assert all(calculo["tarjeta"] == tarjeta_a for calculo in historial_a.json())
    assert historial_b.json() == [respuesta_b]
    assert all(calculo["tarjeta"] == tarjeta_b for calculo in historial_b.json())
    assert all(calculo["tarjeta"] != tarjeta_a for calculo in historial_b.json())
