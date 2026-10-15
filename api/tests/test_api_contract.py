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
            params={"serviceId": "massage-special", "date": tomorrow, "therapistId": "alex"},
        )
        assert availability.status_code == 200
        assert isinstance(availability.json()["slots"], list)
