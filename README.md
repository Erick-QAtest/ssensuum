# SSENSUUM Product · Sprint 1

MVP local de SSENSUUM diseñado para trabajar junto al framework de QA de Playwright.

## Qué incluye

- Frontend Next.js + TypeScript en `http://localhost:3000`
- Backend FastAPI en `http://localhost:8000`
- SQLAlchemy con SQLite por defecto y PostgreSQL opcional
- Catálogo público con precios público/miembro
- Terapeutas
- Flujo inicial de reserva
- Próximos 14 días
- Disponibilidad real por servicio / terapeuta / día
- Regla mínima de 3 horas
- Prevención de doble reserva en el MVP local
- Servicios de 2 terapeutas y anticipo de $600
- Agenda administrativa básica
- Bloqueos de agenda
- Registro de clientes con teléfono único
- Importación de clientes desde Excel o CSV en `/admin/clientes`
- Test IDs compatibles con `ssensuum-qa-framework`

## Qué NO incluye todavía

Este Sprint 1 no implementa aún:

- pasarela de pagos real
- webhook de pago
- cuentas de miembro
- recuperación de contraseña
- membresías
- beneficio de cumpleaños
- WhatsApp
- correo transaccional
- corte de caja completo
- CRM / automatizaciones

Esas piezas pertenecen a los siguientes sprints del producto.

---

## Arranque rápido

Desde la raíz:

```bash
chmod +x scripts/bootstrap.sh scripts/dev.sh
./scripts/bootstrap.sh
./scripts/dev.sh
```

Luego abre:

- Web: http://localhost:3000
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

Para detener ambos procesos usa `Ctrl+C`.

---

## Configurar el framework QA

Si tu framework está en:

```text
~/Downloads/ssensuum-qa-framework
```

puedes ejecutar:

```bash
python3 scripts/configure_qa.py ~/Downloads/ssensuum-qa-framework/.env
```

El script agrega datos QA conocidos del seed local:

- `QA_SERVICE_ID=massage-special`
- `QA_SERVICE_NAME=Masaje especial`
- `QA_THERAPIST_ID=alex`
- `QA_THERAPIST_NAME=Alex`
- fecha de mañana
- horario 12:00
- slot libre para prueba de concurrencia

Después, en el framework QA:

```bash
npm run test:smoke
```

El RF-001 debe poder correr contra el producto local y el flujo RF-010/RF-011/RF-016 deja de quedar bloqueado por falta de datos QA.

---

## Estructura

```text
ssensuum-product/
├── api/
│   ├── app/
│   │   ├── main.py            # app, CORS, manejo de errores, registro de routers
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── serializers.py     # modelos -> JSON del contrato
│   │   ├── seed.py
│   │   ├── routers/           # capa HTTP: health, catalog, availability, reservations, customers, admin
│   │   ├── services/          # casos de uso: availability, reservations, customers, agenda
│   │   ├── repositories/      # consultas SQLAlchemy: catalog, reservations, customers, blocks
│   │   └── domain/            # reglas puras (rules.py) y errores de dominio (errors.py)
│   ├── tests/
│   ├── .env.example
│   └── requirements.txt
├── web/
│   ├── app/                   # rutas de Next.js
│   ├── features/
│   │   ├── catalog/           # Catalog, ServiceRow, categories
│   │   ├── booking/           # BookingClient, dates
│   │   └── customers/         # CustomersPage, ImportPanel
│   ├── components/            # UI compartida (icons)
│   ├── lib/                   # api.ts (cliente HTTP), format.ts, types.ts
│   ├── .env.local.example
│   └── package.json
├── docs/
│   └── QA_CONTRACT.md
└── scripts/
    ├── bootstrap.sh
    ├── configure_qa.py
    ├── dev.sh
    └── reset_dev_db.sh
```

Dependencias en la API: `routers → services → repositories`, y todos pueden usar `domain`. Los servicios lanzan errores de `domain/errors.py`; `main.py` los convierte en respuestas HTTP.

---

## Base de datos

Por defecto usa SQLite para que el producto pueda arrancar sin Docker:

```text
sqlite:///./ssensuum.db
```

Para PostgreSQL cambia `DATABASE_URL` en `api/.env`, por ejemplo:

```env
DATABASE_URL=postgresql+psycopg://ssensuum:ssensuum@localhost:5432/ssensuum
```

Para producción, la prevención de concurrencia debe reforzarse con una estrategia transaccional/constraint a nivel de base de datos. El lock incluido aquí es deliberadamente un mecanismo de MVP local.

---

## Comandos útiles

Backend:

```bash
cd api
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd web
npm run dev
```

Tests backend:

```bash
cd api
source .venv/bin/activate
pytest -q
```

Build frontend:

```bash
cd web
npm run build
```

## Reset de datos locales

Si una prueba de reserva deja ocupado un slot y quieres volver al seed limpio:

```bash
./scripts/reset_dev_db.sh
./scripts/dev.sh
```
