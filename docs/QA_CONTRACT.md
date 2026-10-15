# Contrato QA · Sprint 1

Este producto local fue construido para respetar el contrato inicial del framework `ssensuum-qa-framework`.

## Frontend

### Catálogo

- `data-testid="catalog"`
- `data-testid="service-card"`
- botón accesible con nombre `Reservar`

### Reserva

- `data-testid="therapist-card"`
- botón `Sin preferencia`
- `data-testid="date-YYYY-MM-DD"`
- `data-testid="slot-HH-MM"`
- botón con texto `Continuar al resumen`
- `data-testid="booking-summary"`
- `data-testid="deposit-amount"`

## API

Rutas implementadas:

- `GET /health`
- `GET /services`
- `GET /therapists`
- `GET /availability?serviceId=...&date=...&therapistId=...`
- `POST /reservations`
- `GET /reservations/{reservationId}`
- `PATCH /reservations/{reservationId}/reschedule`
- `GET /admin/agenda?date=...`
- `POST /admin/blocks`
- `DELETE /admin/blocks/{blockId}`
- `GET /customers?q=...&limit=...&offset=...`
- `POST /customers`
- `GET /customers/{customerId}`
- `PATCH /customers/{customerId}`
- `POST /customers/import?dryRun=true|false` (multipart, campo `file`)

### Clientes

- El teléfono es único y se guarda a 10 dígitos; se aceptan espacios, guiones y prefijo `+52`.
- `POST /customers` requiere `phone` y `firstName`; `lastName`, `email` y `birthday` (`YYYY-MM-DD`) son opcionales.
- Teléfono duplicado responde `409`; datos inválidos responden `422`.
- `q` busca por nombre, apellido o teléfono.

### Importación de clientes

- Acepta `.xlsx` y `.csv` de hasta 5 MB y 10 000 filas; la primera fila con datos son los encabezados.
- Requiere una columna de teléfono y una de nombre; apellido, correo y cumpleaños son opcionales.
- `dryRun=true` (valor por defecto) solo revisa el archivo; `dryRun=false` crea los clientes.
- Los teléfonos ya registrados o repetidos en el archivo se omiten; nunca se modifica un cliente existente.
- Las filas sin teléfono válido o sin nombre no se importan. Un correo o cumpleaños inválido se omite y la fila sí se importa.

### Pantalla de clientes (`/admin/clientes`)

- `data-testid="customers-page"`
- `data-testid="customer-row"`
- `data-testid="import-file"`, `import-review`, `import-summary`, `import-valid`, `import-issue`, `import-confirm`, `import-done`

## Seed QA

Servicio estable:

```text
ID: massage-special
Nombre: Masaje especial
Duración: 60 min
Anticipo: 300 MXN
Terapeutas requeridos: 1
```

Terapeuta estable:

```text
ID: jessy
Nombre: Jessy
```
