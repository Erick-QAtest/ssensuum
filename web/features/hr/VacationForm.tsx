'use client';

import { FormEvent, useEffect, useState } from 'react';
import { getStaffOffboarding, setStaffVacation } from '../../lib/api';
import type { StaffMember, StaffOffboarding } from '../../lib/types';
import { todayInput } from './hr';

type Props = {
  member: StaffMember;
  onSaved: () => void;
  onCancel: () => void;
};

const when = (iso: string) => new Date(iso).toLocaleString('es-MX', { weekday: 'short', day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit' });
const localDay = (iso: string) => new Date(iso).toLocaleDateString('en-CA', { timeZone: 'America/Mexico_City' });

// Vacaciones: sigue en el equipo, pero mientras duran no aparece en el sitio ni se le puede reservar.
export function VacationForm({ member, onSaved, onCancel }: Props) {
  const [startsOn, setStartsOn] = useState(member.vacationFrom ?? todayInput());
  const [returnsOn, setReturnsOn] = useState(member.vacationUntil ?? '');
  const [agenda, setAgenda] = useState<StaffOffboarding | null>(null);
  const [notified, setNotified] = useState(false);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getStaffOffboarding(member.id).then(setAgenda).catch((e: Error) => setError(e.message));
  }, [member.id]);

  // Reservas que caen dentro de las vacaciones elegidas.
  const clashes = (agenda?.upcomingReservations ?? []).filter((row) => {
    const day = localDay(row.startsAt);
    return day >= startsOn && (!returnsOn || day < returnsOn);
  });

  function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError('');
    setStaffVacation(member.id, startsOn, returnsOn || null, notified)
      .then(onSaved)
      .catch((e: Error) => setError(e.message))
      .finally(() => setSaving(false));
  }

  return (
    <section className="adminCard" data-testid="vacation-form">
      <h2>Vacaciones de {member.name}</h2>
      <p className="muted">Mientras dure no aparece en el sitio y no se le puede reservar. Sigue en el equipo con su expediente y su horario; el día de regreso vuelve solo.</p>
      <form className="recordForm" onSubmit={submit}>
        <div className="recordGrid">
          <label>Desde<input type="date" value={startsOn} onChange={(event) => setStartsOn(event.target.value)} required /></label>
          <label>Regresa el<input type="date" value={returnsOn} min={startsOn} onChange={(event) => setReturnsOn(event.target.value)} /></label>
        </div>
        <p className="adminSub">Si aún no sabes cuándo regresa, deja vacío “Regresa el” y termínalas desde la tabla cuando vuelva.</p>

        {clashes.length > 0 ? (
          <ul className="hrChecklist">
            <li className={notified ? 'ok' : 'wait'}>
              Tiene {clashes.length === 1 ? '1 reserva' : `${clashes.length} reservas`} en esas fechas. Avisa a cada cliente y acuerda quién lo atiende o si cambia de día:
              <ul>
                {clashes.map((row) => (
                  <li key={row.id}>{when(row.startsAt)} · {row.serviceName}{row.customerName ? ` · ${row.customerName}` : ''}</li>
                ))}
              </ul>
              <label className="hrCheck">
                <input type="checkbox" checked={notified} onChange={(event) => setNotified(event.target.checked)} />
                Ya avisé a estos clientes
              </label>
            </li>
          </ul>
        ) : null}

        {error ? <div className="errorBox" role="alert">{error}</div> : null}
        <div className="adminRow">
          <button type="submit" className="primaryButton" disabled={!agenda || saving || (clashes.length > 0 && !notified)} data-testid="vacation-save">
            {saving ? 'Guardando…' : 'Guardar vacaciones'}
          </button>
          <button type="button" className="secondaryButton" disabled={saving} onClick={onCancel}>Cancelar</button>
        </div>
      </form>
    </section>
  );
}
