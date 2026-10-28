'use client';

import { FormEvent, useEffect, useState } from 'react';
import Link from 'next/link';
import { getStaffOffboarding, staffLeave } from '../../lib/api';
import type { StaffMember, StaffOffboarding } from '../../lib/types';
import { TherapistAvatar } from '../../components/TherapistAvatar';
import { todayInput } from './hr';

type Props = {
  member: StaffMember;
  onDone: () => void;
  onCancel: () => void;
};

const money = (amount: number) => amount.toLocaleString('es-MX', { style: 'currency', currency: 'MXN', maximumFractionDigits: 0 });
const when = (iso: string) => new Date(iso).toLocaleString('es-MX', { weekday: 'short', day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit' });

// Baja en dos pasos: primero se revisa qué queda pendiente con el masajista, después se confirma.
export function LeaveFlow({ member, onDone, onCancel }: Props) {
  const [check, setCheck] = useState<StaffOffboarding | null>(null);
  const [leftOn, setLeftOn] = useState(todayInput);
  const [reason, setReason] = useState('');
  const [notified, setNotified] = useState(false);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setCheck(null);
    getStaffOffboarding(member.id).then(setCheck).catch((e: Error) => setError(e.message));
  }, [member.id]);

  const upcoming = check?.upcomingReservations.length ?? 0;
  const blocked = upcoming > 0 && !notified;

  function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError('');
    staffLeave(member.id, leftOn, reason, notified)
      .then(onDone)
      .catch((e: Error) => setError(e.message))
      .finally(() => setSaving(false));
  }

  return (
    <section className="adminCard" data-testid="leave-flow">
      <div className="hrPerson">
        <TherapistAvatar therapist={member} className="hrAvatar" />
        <h2>Dar de baja a {member.name}</h2>
      </div>
      <p className="muted">Deja de aparecer en el sitio y ya no se le pueden hacer reservas. Su expediente, documentos y pagos se conservan, y puedes reactivarlo cuando quieras.</p>

      <h3 className="hrSubhead">1. Pendientes</h3>
      {check === null && !error ? <p className="muted">Revisando su agenda…</p> : null}
      {check ? (
        <ul className="hrChecklist">
          <li className={blocked ? 'wait' : 'ok'} data-testid="leave-reservations">
            {upcoming > 0 ? (
              <>
                Tiene {upcoming === 1 ? '1 reserva próxima' : `${upcoming} reservas próximas`}. Avisa a cada cliente (desde <Link href="/admin/reservas">Reservas</Link> sale su WhatsApp) y acuerda quién lo atiende o si cambia de horario:
                <ul>
                  {check.upcomingReservations.map((row) => (
                    <li key={row.id}>{when(row.startsAt)} · {row.serviceName}{row.customerName ? ` · ${row.customerName}` : ''}</li>
                  ))}
                </ul>
                <label className="hrCheck">
                  <input type="checkbox" checked={notified} onChange={(event) => setNotified(event.target.checked)} data-testid="leave-notified" />
                  Ya avisé a estos clientes
                </label>
              </>
            ) : 'Sin reservas próximas.'}
          </li>
          <li className={check.pendingPayouts ? 'wait' : 'ok'}>
            {check.pendingPayouts
              ? `Se le deben ${money(check.pendingAmount)} de ${check.pendingPayouts === 1 ? '1 servicio' : `${check.pendingPayouts} servicios`}: liquídalo en la sección de pagos (la baja no lo borra).`
              : 'Sin pagos pendientes.'}
          </li>
          <li className="ok">Recoge uniforme, llaves y cualquier material del club.</li>
        </ul>
      ) : null}

      <h3 className="hrSubhead">2. Confirmar</h3>
      <form className="recordForm" onSubmit={submit}>
        <div className="recordGrid">
          <label>Fecha de baja<input type="date" value={leftOn} onChange={(event) => setLeftOn(event.target.value)} required /></label>
          <label>Motivo<input value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Opcional: renuncia, fin de contrato…" /></label>
        </div>
        {error ? <div className="errorBox" role="alert">{error}</div> : null}
        <div className="adminRow">
          <button type="submit" className="primaryButton hrDanger" disabled={!check || blocked || saving} data-testid="leave-confirm">
            {saving ? 'Dando de baja…' : `Dar de baja a ${member.name}`}
          </button>
          <button type="button" className="secondaryButton" disabled={saving} onClick={onCancel}>Cancelar</button>
        </div>
      </form>
    </section>
  );
}
