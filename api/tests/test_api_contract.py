from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from app.main import app

TZ = ZoneInfo("America/Mexico_City")


def test_catalog_and_availability_contract():
    with TestClient(app) as client:
        services = client.get("/services")
        assert services.status_code == 200
        names = {row["name"] for row in services.json()}
        assert "Masaje especial SSENSUUM" in names

        tomorrow = (datetime.now(TZ) + timedelta(days=1)).date().isoformat()
        availability = client.get(
            "/availability",
            params={"serviceId": "massage-special", "date": tomorrow, "therapistId": "jessy"},
        )
        assert availability.status_code == 200
        assert isinstance(availability.json()["slots"], list)


def test_massages_include_how_it_works():
    with TestClient(app) as client:
        services = {row["id"]: row for row in client.get("/services").json()}
        assert services["swedish"]["details"]
        assert services["massage-special"]["details"]


def test_catalog_offers_only_massages():
    with TestClient(app) as client:
        categories = {row["category"] for row in client.get("/services").json()}
        assert categories == {"Masajes"}


def test_seed_retires_old_barber_and_aesthetics_services():
    from app.db import SessionLocal
    from app.models import Service
    from app.seed import seed

    with TestClient(app):
        pass
    with SessionLocal() as db:
        db.merge(Service(id="botox", name="Botox", category="Medicina estética", description="", duration_minutes=60,
                         public_price=2600, member_price=2050, deposit=300, therapists_required=1, active=True))
        db.commit()
        seed(db)
        assert db.get(Service, "botox").active is False
