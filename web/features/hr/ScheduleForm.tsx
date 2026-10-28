'use client';

import { FormEvent, useState } from 'react';
import { saveStaffSchedule } from '../../lib/api';
import { WEEKDAYS } from '../../lib/schedule';
import type { Schedule, StaffMember } from '../../lib/types';

type Props = {
  member: StaffMember;
  onSaved: () => void;
  onCancel: () => void;
};

type Window = [string, string];
const OPEN: Window = ['09:00', '20:30'];

function initialDays(schedule: Schedule | null): Window[][] {
  return WEEKDAYS.map((_, day) => (schedule && 'days' in schedule ? (schedule.days[String(day)] ?? []).map(([from, to]) => [from, to] as Window) : []));
}

// Fuera de estas franjas el sitio no ofrece horarios con este masajista y la API rechaza la reserva.
export function ScheduleForm({ member, onSaved, onCancel }: Props) {
  const [always, setAlways] = useState(!member.schedule || 'always' in member.schedule);
  const [days, setDays] = useState<Window[][]>(() => initialDays(member.schedule));
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  function update(day: number, windows: Window[]) {
    setDays((current) => current.map((row, index) => (index === day ? windows : row)));
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError('');
    const schedule: Schedule = always
      ? { always: true }
      : { days: Object.fromEntries(days.map((windows, day) => [String(day), windows]).filter(([, windows]) => windows.length)) };
    saveStaffSchedule(member.id, schedule)
      .then(onSaved)
      .catch((e: Error) => setError(e.message))
      .finally(() => setSaving(false));
  }

  return (
    <section className="adminCard" data-testid="schedule-form">
      <h2>Horario de {member.name}</h2>
      <p className="muted">Solo se le podrá reservar dentro de estas horas, y la sesión completa debe caber en la franja. El club abre de 9 am a 8:30 pm.</p>
      <form className="recordForm" onSubmit={submit}>
        <div className="hrScheduleMode" role="radiogroup" aria-label="Disponibilidad">
          <label className="hrCheck"><input type="radio" checked={always} onChange={() => setAlways(true)} /> Siempre disponible</label>
          <label className="hrCheck"><input type="radio" checked={!always} onChange={() => setAlways(false)} data-testid="schedule-custom" /> Días y horas específicos</label>
        </div>

        {!always ? (
          <ul className="hrSchedule">
            {WEEKDAYS.map((label, day) => (
              <li key={label} data-testid="schedule-day">
                <label className="hrCheck">
                  <input type="checkbox" checked={days[day].length > 0} onChange={(event) => update(day, event.target.checked ? [OPEN] : [])} />
                  {label}
                </label>
                <div className="hrScheduleWindows">
                  {days[day].length === 0 ? <span className="adminSub">Descanso</span> : null}
                  {days[day].map(([from, to], index) => (
                    <span key={index} className="hrScheduleWindow">
                      <input type="time" step={1800} value={from} aria-label={`${label}: entrada`} onChange={(event) => update(day, days[day].map((row, i) => (i === index ? [event.target.value, row[1]] : row)))} required />
                      <span>a</span>
                      <input type="time" step={1800} value={to} aria-label={`${label}: salida`} onChange={(event) => update(day, days[day].map((row, i) => (i === index ? [row[0], event.target.value] : row)))} required />
                      {days[day].length > 1 ? <button type="button" className="hrLink" onClick={() => update(day, days[day].filter((_, i) => i !== index))}>Quitar</button> : null}
                    </span>
                  ))}
                  {days[day].length > 0 ? <button type="button" className="hrLink" onClick={() => update(day, [...days[day], ['15:00', '16:00']])}>+ Otra franja</button> : null}
                </div>
              </li>
            ))}
          </ul>
        ) : null}

        {error ? <div className="errorBox" role="alert">{error}</div> : null}
        <div className="adminRow">
          <button type="submit" className="primaryButton" disabled={saving} data-testid="schedule-save">{saving ? 'Guardando…' : 'Guardar horario'}</button>
          <button type="button" className="secondaryButton" disabled={saving} onClick={onCancel}>Cancelar</button>
        </div>
      </form>
    </section>
  );
}
