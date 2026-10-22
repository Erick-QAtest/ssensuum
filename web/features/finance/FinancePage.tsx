'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { AdminNav } from '../../components/AdminNav';
import { deleteFinanceMovement, financeExportUrl, getFinanceDashboard, getFinanceMeta, getFinanceMovements, getFinanceStatements } from '../../lib/api';
import { money } from '../../lib/format';
import type { FinanceDashboard as Dashboard, FinanceMeta, FinanceMovement, FinanceStatements } from '../../lib/types';
import { localIsoDate } from '../booking/dates';
import { formatDate } from '../hr/hr';
import { FinanceDashboard } from './FinanceDashboard';
import { MovementForm } from './MovementForm';
import { Statement, StatementRow } from './Statement';

type Period = 'mes' | 'mes-anterior' | 'anio' | 'personalizado';

function range(period: Period, custom: { from: string; to: string }) {
  const today = new Date();
  if (period === 'mes') return { from: localIsoDate(new Date(today.getFullYear(), today.getMonth(), 1)), to: localIsoDate(today) };
  if (period === 'mes-anterior') {
    return {
      from: localIsoDate(new Date(today.getFullYear(), today.getMonth() - 1, 1)),
      to: localIsoDate(new Date(today.getFullYear(), today.getMonth(), 0)),
    };
  }
  if (period === 'anio') return { from: localIsoDate(new Date(today.getFullYear(), 0, 1)), to: localIsoDate(today) };
  return custom;
}

const PERIODS: { id: Period; label: string }[] = [
  { id: 'mes', label: 'Este mes' },
  { id: 'mes-anterior', label: 'Mes anterior' },
  { id: 'anio', label: 'Este año' },
  { id: 'personalizado', label: 'Personalizado' },
];

function incomeRows(data: FinanceStatements): StatementRow[] {
  const pnl = data.incomeStatement;
  return [
    { label: 'Ingresos por servicios', amount: pnl.revenue },
    { label: 'Honorarios de masajistas', amount: -pnl.costOfServices },
    { label: 'Utilidad bruta', amount: pnl.grossProfit, kind: 'subtotal' },
    { label: 'Gastos de operación', kind: 'section' },
    ...(pnl.expenses.length ? pnl.expenses.map((row) => ({ label: row.label, amount: -row.amount })) : [{ label: 'Sin gastos capturados', amount: 0 }]),
    { label: 'Total gastos de operación', amount: -pnl.operatingExpenses, kind: 'subtotal' },
    { label: 'Utilidad de operación', amount: pnl.operatingIncome, kind: 'subtotal' },
    ...(pnl.otherIncome.length ? [{ label: 'Otros ingresos', kind: 'section' as const }, ...pnl.otherIncome.map((row) => ({ label: row.label, amount: row.amount }))] : []),
    { label: 'Utilidad neta', amount: pnl.netIncome, kind: 'total' },
  ];
}

function cashRows(data: FinanceStatements): StatementRow[] {
  const flow = data.cashFlow;
  return [
    { label: 'Efectivo al inicio del periodo', amount: flow.opening, kind: 'subtotal' },
    ...flow.sections.flatMap((section) => [
      { label: section.label, kind: 'section' as const },
      ...section.items.map((item) => ({ label: item.label, amount: item.amount })),
      { label: `Flujo de ${section.label.toLowerCase()}`, amount: section.total, kind: 'subtotal' as const },
    ]),
    { label: 'Cambio neto del periodo', amount: flow.netChange, kind: 'subtotal' },
    { label: 'Efectivo al final del periodo', amount: flow.closing, kind: 'total' },
  ];
}

function balanceRows(data: FinanceStatements): StatementRow[] {
  const sheet = data.balanceSheet;
  return [
    { label: 'Activo', kind: 'section' },
    ...sheet.assets.map((row) => ({ label: row.label, amount: row.amount })),
    { label: 'Total activo', amount: sheet.totalAssets, kind: 'total' },
    { label: 'Pasivo', kind: 'section' },
    ...(sheet.liabilities.length ? sheet.liabilities.map((row) => ({ label: row.label, amount: row.amount })) : [{ label: 'Sin deudas', amount: 0 }]),
    { label: 'Total pasivo', amount: sheet.totalLiabilities, kind: 'subtotal' },
    { label: 'Capital', kind: 'section' },
    ...sheet.equity.map((row) => ({ label: row.label, amount: row.amount })),
    { label: 'Total capital', amount: sheet.totalEquity, kind: 'subtotal' },
    { label: 'Pasivo más capital', amount: sheet.totalLiabilities + sheet.totalEquity, kind: 'total' },
  ];
}

export function FinancePage() {
  const [meta, setMeta] = useState<FinanceMeta | null>(null);
  const [period, setPeriod] = useState<Period>('mes');
  const [custom, setCustom] = useState(() => range('mes', { from: '', to: '' }));
  const [data, setData] = useState<FinanceStatements | null>(null);
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [loading, setLoading] = useState(false);
  const [movements, setMovements] = useState<FinanceMovement[] | null>(null);
  const [error, setError] = useState('');

  const { from, to } = useMemo(() => range(period, custom), [period, custom]);

  useEffect(() => {
    getFinanceMeta().then(setMeta).catch((e: Error) => setError(e.message));
  }, []);

  const load = useCallback(() => {
    if (!from || !to || to < from) return Promise.resolve();
    // Mientras recarga, se conserva lo anterior atenuado: sin parpadeos ni saltos.
    setLoading(true);
    return Promise.all([getFinanceStatements(from, to), getFinanceMovements(from, to), getFinanceDashboard(from, to)])
      .then(([statements, rows, board]) => { setData(statements); setMovements(rows); setDashboard(board); setError(''); })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [from, to]);

  useEffect(() => { load(); }, [load]);

  function remove(movement: FinanceMovement) {
    if (!window.confirm(`¿Borrar “${movement.description}” por ${money(movement.amount)}?`)) return;
    deleteFinanceMovement(movement.id).then(load).catch((e: Error) => setError(e.message));
  }

  return (
    <main className="bookingShell" data-testid="finance-page">
      <Link href="/" className="backLink">← Volver al sitio</Link>
      <div className="bookingPanel">
        <div className="bookingTitle">
          <span className="kicker">Administración</span>
          <h1>Finanzas</h1>
        </div>
        <AdminNav current="finanzas" />

        <div className="adminRow" role="group" aria-label="Periodo">
          {PERIODS.map((option) => (
            <button key={option.id} type="button" className={`secondaryButton ${period === option.id ? 'selected' : ''}`} aria-pressed={period === option.id} onClick={() => setPeriod(option.id)}>
              {option.label}
            </button>
          ))}
        </div>
        {period === 'personalizado' ? (
          <div className="adminRow recordForm financeDates">
            <label>Desde<input type="date" value={custom.from} onChange={(event) => setCustom({ ...custom, from: event.target.value })} /></label>
            <label>Hasta<input type="date" value={custom.to} onChange={(event) => setCustom({ ...custom, to: event.target.value })} /></label>
          </div>
        ) : null}
        <div className="adminRow adminRowSpread financePeriod">
          <strong>{from && to ? `${formatDate(from)} – ${formatDate(to)}` : 'Elige las fechas'}</strong>
          {from && to && to >= from ? <a className="secondaryButton hrButtonLink" href={financeExportUrl(from, to)} data-testid="finance-export">Exportar a Excel</a> : null}
        </div>
        {to && from && to < from ? <div className="errorBox" role="alert">La fecha final debe ser posterior a la inicial.</div> : null}
        {data && from < data.startDate ? (
          <p className="muted">La contabilidad automática empieza el {formatDate(data.startDate)}, con los contratos del equipo. Antes de esa fecha solo cuentan los movimientos capturados.</p>
        ) : null}
        {error ? <div className="errorBox" role="alert">{error}</div> : null}

        <div className={loading ? 'financeLoading' : ''}>
          {dashboard ? <FinanceDashboard data={dashboard} /> : null}

        {data ? (
          <div className="financeGrid">
            <h2 className="financeSectionTitle">Estados financieros</h2>
            <section className="adminCard">
              <h2>Estado de resultados</h2>
              <p className="muted">Lo que se ganó en el periodo: servicios cobrados menos honorarios y gastos.</p>
              <Statement rows={incomeRows(data)} testId="income-statement" />
            </section>

            <section className="adminCard">
              <h2>Flujo de efectivo</h2>
              <p className="muted">El dinero que entró y salió de caja, banco y Mercado Pago.</p>
              <Statement rows={cashRows(data)} testId="cash-flow" />
              <div className="adminTableWrap">
                <table className="adminTable">
                  <thead><tr><th>Cuenta</th><th className="financeAmount">Inicio</th><th className="financeAmount">Final</th></tr></thead>
                  <tbody>
                    {data.cashFlow.accounts.map((row) => (
                      <tr key={row.account}><td>{row.label}</td><td className="financeAmount">{money(row.opening)}</td><td className="financeAmount">{money(row.closing)}</td></tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="adminCard">
              <div className="adminRow adminRowSpread">
                <h2>Balance general</h2>
                <span className={`statusBadge ${data.balanceSheet.balanced ? 'ok' : 'alert'}`} data-testid="balance-check">
                  {data.balanceSheet.balanced ? 'Cuadra' : 'No cuadra'}
                </span>
              </div>
              <p className="muted">Lo que tiene y lo que debe el negocio al {formatDate(data.to)}.</p>
              <Statement rows={balanceRows(data)} testId="balance-sheet" />
            </section>
          </div>
        ) : null}
        </div>

        <section className="adminCard">
          <h2>Registrar movimiento</h2>
          <p className="muted">
            Los servicios, las propinas y los pagos al equipo entran solos desde Registro y Equipo. Aquí se capturan los gastos y todo lo demás que mueve dinero.
          </p>
          {meta ? <MovementForm meta={meta} onSaved={load} /> : null}

          <h3 className="hrSubhead">Movimientos del periodo</h3>
          {movements?.length === 0 ? <p className="muted">No hay movimientos capturados en este periodo.</p> : null}
          {movements && movements.length > 0 ? (
            <div className="adminTableWrap">
              <table className="adminTable">
                <thead><tr><th>Fecha</th><th>Movimiento</th><th>Cuenta</th><th className="financeAmount">Importe</th><th></th></tr></thead>
                <tbody>
                  {movements.map((movement) => (
                    <tr key={movement.id} data-testid="finance-movement-row">
                      <td>{formatDate(movement.day)}</td>
                      <td>{movement.description}<span className="adminSub">{movement.kindLabel}{movement.categoryLabel ? ` · ${movement.categoryLabel}` : ''}</span></td>
                      <td>{movement.accountLabel}{movement.toAccountLabel ? ` → ${movement.toAccountLabel}` : ''}</td>
                      <td className="financeAmount">{money(movement.amount)}</td>
                      <td className="recordActions"><button type="button" className="linkButton" onClick={() => remove(movement)}>Borrar</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </section>
      </div>
    </main>
  );
}
