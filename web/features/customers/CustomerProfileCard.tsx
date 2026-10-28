'use client';

import { useEffect, useRef, useState } from 'react';
import { getCustomerProfile, updateCustomerSource } from '../../lib/api';
import { money } from '../../lib/format';
import type { CustomerProfile, MarketingOption } from '../../lib/types';
import { QUESTIONS, TIME_WINDOWS, type TimeWindow } from '../quiz/quiz';
import { StageBadge } from './stages';

const RECURRENCE_STATUS = {
  al_corriente: { label: 'Al corriente', tone: 'ok' },
  atrasado: { label: 'Se tardó más de lo normal', tone: 'alert' },
  inactivo: { label: 'Inactivo', tone: 'alert' },
} as const;

function dateLabel(iso: string | null) {
  if (!iso) return '—';
  const [year, month, day] = iso.slice(0, 10).split('-').map(Number);
  return new Date(year, month - 1, day).toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric' });
}

function dateTimeLabel(iso: string) {
  return new Date(iso).toLocaleString('es-MX', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'America/Mexico_City' });
}

function times(count: number) {
  return count === 1 ? '1 vez' : `${count} veces`;
}

function quizAnswer(questionId: string, value: string | undefined) {
  const question = QUESTIONS.find((row) => row.id === questionId);
  return question?.options.find((option) => option.value === value)?.label ?? value;
}

function Fact({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{children}</dd>
    </div>
  );
}

type Props = { customerId: string; sources: MarketingOption[]; onClose: () => void; onSourceChanged: () => void };

export function CustomerProfileCard({ customerId, sources, onClose, onSourceChanged }: Props) {
  const [profile, setProfile] = useState<CustomerProfile | null>(null);
  const [error, setError] = useState('');
  const headingRef = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    setProfile(null);
    setError('');
    getCustomerProfile(customerId).then(setProfile).catch((e: Error) => setError(e.message));
  }, [customerId]);

  useEffect(() => {
    if (!profile) return;
    headingRef.current?.focus({ preventScroll: true });
    headingRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, [profile]);

  async function changeSource(value: string) {
    if (!profile) return;
    setError('');
    try {
      const updated = await updateCustomerSource(profile.id, value || null);
      setProfile({ ...profile, acquisitionSource: updated.acquisitionSource });
      onSourceChanged();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  const recurrence = profile?.recurrence;
  const prefs = profile?.preferences;
  const status = recurrence?.status ? RECURRENCE_STATUS[recurrence.status] : null;
  const quizEntries = profile ? QUESTIONS.filter((question) => profile.quiz[question.id]) : [];

  return (
    <section className="adminCard customerProfile" aria-labelledby="customer-profile-title" data-testid="customer-profile">
      <div className="adminRow adminRowSpread">
        <div>
          <h2 id="customer-profile-title" ref={headingRef} tabIndex={-1}>
            {profile ? `${profile.firstName} ${profile.lastName}`.trim() : 'Ficha del cliente'}
          </h2>
          {profile ? <StageBadge stage={profile.stage} /> : null}
        </div>
        <button type="button" className="hrLink" onClick={onClose}>Cerrar ficha</button>
      </div>

      {error ? <div className="errorBox" role="alert">{error}</div> : null}
      {!profile && !error ? <p className="muted">Cargando ficha…</p> : null}

      {profile && recurrence && prefs ? (
        <>
          <div className="profileGrid">
            <div className="profileBlock">
              <h3>Recurrencia</h3>
              {recurrence.visits === 0 ? (
                <p className="muted">Aún no tiene visitas registradas.</p>
              ) : (
                <dl className="profileFacts">
                  <Fact label="Visitas">{recurrence.visits}</Fact>
                  <Fact label="Primera visita">{dateLabel(recurrence.firstVisit)}</Fact>
                  <Fact label="Última visita">
                    {dateLabel(recurrence.lastVisit)}
                    <span className="adminSub">hace {recurrence.daysSinceLastVisit} días</span>
                  </Fact>
                  <Fact label="Frecuencia">{recurrence.averageGapDays ? `Cada ${recurrence.averageGapDays} días en promedio` : 'Aún no hay frecuencia: solo una visita'}</Fact>
                  <Fact label="Debería volver">{dateLabel(recurrence.nextExpectedVisit)}</Fact>
                  {status ? <Fact label="Estado"><span className={`statusBadge stage-${status.tone}`}>{status.label}</span></Fact> : null}
                </dl>
              )}
              {profile.upcoming.length ? (
                <p className="profileNote">
                  Próxima cita: {dateTimeLabel(profile.upcoming[0].startsAt)} · {profile.upcoming[0].serviceName}
                  {profile.upcoming[0].status === 'PENDING_PAYMENT' ? ' (apartado sin pagar)' : ''}
                </p>
              ) : null}
            </div>

            <div className="profileBlock">
              <h3>Preferencias</h3>
              <dl className="profileFacts">
                <Fact label="Masaje más tomado">{prefs.service ? `${prefs.service.value} · ${times(prefs.service.count)}` : '—'}</Fact>
                <Fact label="Terapeuta favorito">{prefs.therapistId ? `${prefs.therapistId.label ?? prefs.therapistId.value} · ${times(prefs.therapistId.count)}` : '—'}</Fact>
                <Fact label="Día habitual">{prefs.weekday ? prefs.weekday.value.replace(/^./, (c) => c.toUpperCase()) : '—'}</Fact>
                <Fact label="Horario habitual">{prefs.timeWindow ? TIME_WINDOWS[prefs.timeWindow.value as TimeWindow]?.label ?? prefs.timeWindow.value : '—'}</Fact>
                <Fact label="Cómo nos conoció">
                  <select
                    className="profileSource"
                    value={profile.acquisitionSource ?? ''}
                    onChange={(event) => changeSource(event.target.value)}
                    aria-label="Cómo nos conoció"
                    data-testid="profile-source"
                  >
                    <option value="">Sin registrar</option>
                    {sources.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}
                  </select>
                </Fact>
                <Fact label="Membresía">
                  {profile.membershipExpiresOn
                    ? `${profile.member ? 'Vigente hasta' : 'Vencida el'} ${dateLabel(profile.membershipExpiresOn)}`
                    : 'Sin membresía'}
                </Fact>
                <Fact label="Gasto total">
                  {money(prefs.totalSpent)}
                  {prefs.averageTicket ? <span className="adminSub">{money(prefs.averageTicket)} por visita · {money(prefs.totalTips)} en propinas</span> : null}
                </Fact>
              </dl>
            </div>

            <div className="profileBlock">
              <h3>Quiz</h3>
              {quizEntries.length === 0 ? (
                <p className="muted">No ha hecho el quiz antes de reservar.</p>
              ) : (
                <dl className="profileFacts">
                  {quizEntries.map((question) => (
                    <Fact key={question.id} label={question.title}>{quizAnswer(question.id, profile.quiz[question.id])}</Fact>
                  ))}
                </dl>
              )}
              {profile.quizAt ? <p className="adminSub">Respondido el {dateLabel(profile.quizAt)}</p> : null}
            </div>
          </div>

          {profile.history.length ? (
            <>
              <h3 className="hrSubhead">Historial</h3>
              <div className="adminTableWrap">
                <table className="adminTable">
                  <thead><tr><th>Fecha</th><th>Servicio</th><th>Terapeuta</th><th>Cobro</th><th>Propina</th></tr></thead>
                  <tbody>
                    {profile.history.map((visit) => (
                      <tr key={`${visit.at}-${visit.serviceName}`}>
                        <td>{dateTimeLabel(visit.at)}</td>
                        <td>{visit.serviceName}</td>
                        <td>{visit.therapistNames.join(', ') || '—'}</td>
                        <td>{visit.amount === null ? <span className="adminSub">Reserva sin registro</span> : money(visit.amount)}</td>
                        <td>{visit.tip ? money(visit.tip) : '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : null}
        </>
      ) : null}
    </section>
  );
}
