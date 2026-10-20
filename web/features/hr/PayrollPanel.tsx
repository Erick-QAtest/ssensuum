'use client';

import { Fragment, useEffect, useState } from 'react';
import { getWeeklyPayroll, hrPayrollExportUrl } from '../../lib/api';
import { money } from '../../lib/format';
import type { WeeklyPayroll } from '../../lib/types';
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

export function PayrollPanel() {
  const thisWeek = localIsoDate(monday(new Date()));
  const [week, setWeek] = useState(thisWeek);
  const [payroll, setPayroll] = useState<WeeklyPayroll | null>(null);
  const [open, setOpen] = useState<string | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    setPayroll(null);
    setOpen(null);
    getWeeklyPayroll(week)
      .then((body) => { setPayroll(body); setError(''); })
      .catch((e: Error) => setError(e.message));
  }, [week]);

  return (
    <section className="adminCard" data-testid="hr-payroll">
      <div className="adminRow adminRowSpread">
        <h2>Liquidación semanal</h2>
        <a className="secondaryButton hrButtonLink" href={hrPayrollExportUrl(week)} data-testid="hr-export-payroll">Exportar a Excel</a>
      </div>
      <p className="muted">$500 por servicio a cada masajista que lo atendió. La limpieza de $100 se descuenta de su primer servicio de la semana; si no trabajó, no se cobra. Las propinas se pagan completas.</p>

      <div className="adminRow" role="group" aria-label="Semana">
        <button type="button" className="secondaryButton" onClick={() => setWeek(shiftWeek(week, -1))}>← Anterior</button>
        <strong className="hrWeek">{payroll ? `${formatDate(payroll.weekStart)} – ${formatDate(payroll.weekEnd)}` : '…'}</strong>
        <button type="button" className="secondaryButton" onClick={() => setWeek(shiftWeek(week, 1))} disabled={week >= thisWeek}>Siguiente →</button>
        {week !== thisWeek ? <button type="button" className="hrLink" onClick={() => setWeek(thisWeek)}>Esta semana</button> : null}
      </div>

      {error ? <div className="errorBox" role="alert">{error}</div> : null}
      {payroll === null && !error ? <p className="muted">Calculando…</p> : null}
      {payroll?.staff.length === 0 ? <p className="muted">No hay servicios registrados esta semana.</p> : null}

      {payroll && payroll.staff.length > 0 ? (
        <>
          <dl className="adminStats">
            <div><strong>{payroll.totals.services}</strong><span>Servicios por masajista</span></div>
            <div><strong>{money(payroll.totals.servicePay)}</strong><span>Pago por servicios</span></div>
            <div><strong>{money(payroll.totals.total)}</strong><span>Total a pagar con propinas</span></div>
          </dl>
          <div className="adminTableWrap">
            <table className="adminTable">
              <thead><tr><th>Masajista</th><th>Servicios</th><th>Por servicios</th><th>Limpieza</th><th>Propinas</th><th>Total a pagar</th><th></th></tr></thead>
              <tbody>
                {payroll.staff.map((row) => (
                  <Fragment key={row.therapistId}>
                    <tr data-testid="payroll-row">
                      <td>{row.therapistName}</td>
                      <td>{row.services}</td>
                      <td>{money(row.gross)}</td>
                      <td>{row.cleaning ? `−${money(row.cleaning)}` : '—'}</td>
                      <td>{row.tips ? money(row.tips) : '—'}</td>
                      <td><strong>{money(row.total)}</strong></td>
                      <td className="recordActions">
                        {row.lines.length > 0 ? (
                          <button type="button" className="hrLink" aria-expanded={open === row.therapistId} onClick={() => setOpen(open === row.therapistId ? null : row.therapistId)}>
                            {open === row.therapistId ? 'Ocultar' : 'Ver detalle'}
                          </button>
                        ) : null}
                      </td>
                    </tr>
                    {open === row.therapistId ? row.lines.map((line) => (
                      <tr key={`${row.therapistId}-${line.recordId}`} className="hrDetail">
                        <td colSpan={2}>{paidAtLabel(line.paidAt)}</td>
                        <td colSpan={2}>{line.serviceName}<span className="adminSub">{line.customerName}</span></td>
                        <td colSpan={3}>{money(line.pay)}{line.cleaning ? <span className="adminSub">{`${money(line.gross)} − ${money(line.cleaning)} de limpieza`}</span> : null}</td>
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
