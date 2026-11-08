import os
import tempfile

# Las pruebas usan una base temporal para no tocar api/ssensuum.db.
# Debe definirse antes de importar app.*, que lee la configuración al cargar.
_tmp = tempfile.mkdtemp(prefix="ssensuum-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["HR_FILES_DIR"] = f"{_tmp}/rh"
os.environ["TEAM_PHOTOS_DIR"] = f"{_tmp}/equipo"
os.environ["OPS_PHOTOS_DIR"] = f"{_tmp}/operacion"

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def free_cabin_after_each_test():
    """El club tiene una sola cabina: cada prueba deja libre la agenda para que las
    reservas de una no le ocupen el horario a la siguiente."""
    yield
    from app.db import SessionLocal
    from app.models import Reservation

    with SessionLocal() as db:
        db.query(Reservation).filter(Reservation.status.not_in(["CANCELLED", "RESCHEDULED"])).update(
            {Reservation.status: "CANCELLED"}, synchronize_session=False
        )
        db.commit()
