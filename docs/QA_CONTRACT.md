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
ID: alex
Nombre: Alex
```
