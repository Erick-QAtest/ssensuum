import os
import tempfile

# Las pruebas usan una base temporal para no tocar api/ssensuum.db.
# Debe definirse antes de importar app.*, que lee la configuración al cargar.
_tmp = tempfile.mkdtemp(prefix="ssensuum-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["HR_FILES_DIR"] = f"{_tmp}/rh"
os.environ["TEAM_PHOTOS_DIR"] = f"{_tmp}/equipo"
