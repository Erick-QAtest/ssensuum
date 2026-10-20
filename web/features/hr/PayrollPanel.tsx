'use client';

import { Fragment, useCallback, useEffect, useState } from 'react';
import { getPendingPayouts, getWeeklyPayroll, hrPayrollExportUrl, setPayout } from '../../lib/api';
import { money } from '../../lib/format';
import type { PayrollLine, PendingPayout, WeeklyPayroll } from '../../lib/types';
import { localIsoDate } from '../booking/dates';
import { paidAtLabel } from '../records/records';
import { formatDate } from './hr';

// Lunes de la semana de esa fecha: las semanas van de lunes a domingo.
function monday(date: Date) {
  const day = new Date(date);
  day.setDate(day.getDate() - ((day.getDay() + 6) % 7));
  return day;
}

function shiftWeek(iso: string, weeks: number) {
  const [year, month, day] = iso.split('-').map(Number);
  return localIsoDate(new Date(year, month - 1, day + weeks * 7));
}

// Desglose de lo que se paga por un servicio: honorarios − limpieza + propina.
function breakdown(line: PayrollLine) {
  const parts = [money(line.gross)];
  if (line.cleaning) parts.push(`− ${money(line.cleaning)} limpieza`);
  if (line.tip) parts.push(`+ ${money(line.tip)} propina`);
  return parts.length > 1 ? parts.join(' ') : null;
}

function PayoutStatus({ line, busy, onToggle }: { line: PayrollLine; busy: boolean; onToggle: (paid: boolean) => void }) {
  if (line.payoutAt) {
    return (
      <>
        <span className="statusBadge ok">Pagado {paidAtLabel(line.payoutAt)}</span>
        <button type="button" className="hrLink hrUndo" disabled={busy} onClick={() => onToggle(false)}>Deshacer</button>
      </>
    );
  }
  return (
    <>
      <span className={`statusBadge ${line.overdue ? 'alert' : 'wait'}`}>{line.overdue ? 'Vencido' : 'Pendiente'}</span>
      <span className="adminSub">Pagar antes de {paidAtLabel(line.dueAt)}</span>
      <button type="button" className="hrLink" disabled={busy} onClick={() => onToggle(true)}>Marcar pagado</button>
    </>
  );
}

export function PayrollPanel() {
  const thisWeek = localIsoDate(monday(new Date()));
  const [week, setWeek] = useState(thisWeek);
  const [payroll, setPayroll] = useState<WeeklyPayroll | null>(null);
  const [pending, setPending] = useState<PendingPayout[] | null>(null);
  const [open, setOpen] = useState<string | null>(null);
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');

  const load = useCallback(() => {
    return Promise.all([getWeeklyPayroll(week), getPendingPayouts()])
      .then(([weekly, unpaid]) => { setPayroll(weekly); setPending(unpaid); setError(''); })
      .catch((e: Error) => setError(e.message));
  }, [week]);

  useEffect(() => {
    setPayroll(null);
    setOpen(null);
    load();
  }, [load]);

  function toggle(recordId: string, therapistId: string, paid: boolean) {
    const key = `${recordId}-${therapistId}`;
    setBusy(key);
    setPayout(recordId, therapistId, paid)
      .then(load)
      .catch((e: Error) => setError(e.message))
      .finally(() => setBusy(''));
  }

  const overdue = pending?.filter((line) => line.overdue).length ?? 0;

  return (
    <section className="adminCard" data-testid="hr-payroll">
      <div className="adminRow adminRowSpread">
        <h2>Pagos al equipo</h2>
        <a className="secondaryButton hrButtonLink" href={hrPayrollExportUrl(week)} data-testid="hr-export-payroll">Exportar semana a Excel</a>
      </div>
      <p className="muted">
        Cada servicio se paga dentro de las 48 horas: $500 de honorarios más la propina completa. La limpieza de $100 se descuenta del primer servicio de la semana solo a quien firmó la autorización de descuento; a los demás se les cobra aparte, a más tardar el lunes siguiente.
      </p>

      {error ? <div className="errorBox" role="alert">{error}</div> : null}

      <h3 className="hrSubhead">Por pagar {pending && pending.length > 0 ? `(${pending.length}${overdue ? `, ${overdue} vencidos` : ''})` : ''}</h3>
      {pending === null && !error ? <p className="muted">Cargando…</p> : null}
      {pending?.length === 0 ? <p className="muted">No hay pagos pendientes.</p> : null}
      {pending && pending.length > 0 ? (
        <div className="adminTableWrap">
          <table className="adminTable">
            <thead><tr><th>Masajista</th><th>Servicio</th><th>A pagar</th><th>Estado</th></tr></thead>
            <tbody>
              {pending.map((line) => (
                <tr key={`${line.recordId}-${line.therapistId}`} data-testid="payout-pending-row">
                  <td>{line.therapistName}</td>
                  <td>{line.serviceName}<span className="adminSub">{paidAtLabel(line.paidAt)} · {line.customerName}</span></td>
                  <td><strong>{money(line.pay)}</strong>{breakdown(line) ? <span className="adminSub">{breakdown(line)}</span> : null}</td>
                  <td className="hrPayout">
                    <PayoutStatus line={line} busy={busy === `${line.recordId}-${line.therapistId}`} onToggle={(paid) => toggle(line.recordId, line.therapistId, paid)} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      <h3 className="hrSubhead">Resumen semanal</h3>
      <div className="adminRow" role="group" aria-label="Semana">
        <button type="button" className="secondaryButton" onClick={() => setWeek(shiftWeek(week, -1))}>← Anterior</button>
        <strong className="hrWeek">{payroll ? `${formatDate(payroll.weekStart)} – ${formatDate(payroll.weekEnd)}` : '…'}</strong>
        <button type="button" className="secondaryButton" onClick={() => setWeek(shiftWeek(week, 1))} disabled={week >= thisWeek}>Siguiente →</button>
        {week !== thisWeek ? <button type="button" className="hrLink" onClick={() => setWeek(thisWeek)}>Esta semana</button> : null}
      </div>

      {payroll === null && !error ? <p className="muted">Calculando…</p> : null}
      {payroll?.staff.length === 0 ? <p className="muted">No hay servicios registrados esta semana.</p> : null}

      {payroll && payroll.staff.length > 0 ? (
        <>
          <dl className="adminStats">
            <div><strong>{money(payroll.totals.total)}</strong><span>Total de la semana</span></div>
            <div className={payroll.totals.pending ? 'alert' : ''}><strong>{money(payroll.totals.pending)}</strong><span>Falta por pagar</span></div>
            <div><strong>{money(payroll.totals.cleaningToCollect)}</strong><span>Limpieza por cobrar aparte</span></div>
          </dl>
          <div className="adminTableWrap">
            <table className="adminTable">
              <thead><tr><th>Masajista</th><th>Servicios</th><th>Honorarios</th><th>Limpieza</th><th>Propinas</th><th>Total</th><th>Pagado</th><th></th></tr></thead>
              <tbody>
                {payroll.staff.map((row) => (
                  <Fragment key={row.therapistId}>
                    <tr data-testid="payroll-row">
                      <td>{row.therapistName}</td>
                      <td>{row.services}</td>
                      <td>{money(row.gross)}</td>
                      <td>
                        {row.cleaning ? `−${money(row.cleaning)}` : null}
                        {row.cleaningToCollect ? <>{money(row.cleaningToCollect)}<span className="adminSub">Por cobrar aparte</span></> : null}
                        {!row.cleaning && !row.cleaningToCollect ? '—' : null}
                      </td>
                      <td>{row.tips ? money(row.tips) : '—'}</td>
                      <td><strong>{money(row.total)}</strong></td>
                      <td>{row.paidLines} de {row.services}{row.pending ? <span className="adminSub">Falta {money(row.pending)}</span> : null}</td>
                      <td className="recordActions">
                        <button type="button" className="hrLink" aria-expanded={open === row.therapistId} onClick={() => setOpen(open === row.therapistId ? null : row.therapistId)}>
                          {open === row.therapistId ? 'Ocultar' : 'Ver detalle'}
                        </button>
                      </td>
                    </tr>
                    {open === row.therapistId ? row.lines.map((line) => (
                      <tr key={`${row.therapistId}-${line.recordId}`} className="hrDetail">
                        <td colSpan={2}>{paidAtLabel(line.paidAt)}</td>
                        <td colSpan={2}>{line.serviceName}<span className="adminSub">{line.customerName}</span></td>
                        <td colSpan={2}>{money(line.pay)}{breakdown(line) ? <span className="adminSub">{breakdown(line)}</span> : null}</td>
                        <td colSpan={2} className="hrPayout">
                          <PayoutStatus line={line} busy={busy === `${line.recordId}-${row.therapistId}`} onToggle={(paid) => toggle(line.recordId, row.therapistId, paid)} />
                        </td>
                      </tr>
                    )) : null}
                  </Fragment>
                ))}
                <tr className="hrTotal">
                  <td>Total</td>
                  <td>{payroll.totals.services}</td>
                  <td>{money(payroll.totals.gross)}</td>
                  <td>{payroll.totals.cleaning ? `−${money(payroll.totals.cleaning)}` : '—'}</td>
                  <td>{money(payroll.totals.tips)}</td>
                  <td>{money(payroll.totals.total)}</td>
                  <td>{payroll.totals.pending ? `Falta ${money(payroll.totals.pending)}` : 'Todo pagado'}</td>
                  <td></td>
                </tr>
              </tbody>
            </table>
          </div>
        </>
      ) : null}
    </section>
  );
}
