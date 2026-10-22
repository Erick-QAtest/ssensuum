'use client';

import { useMemo } from 'react';
import { money } from '../../lib/format';
import type { FinanceDashboard as Dashboard } from '../../lib/types';
import { formatDate } from '../hr/hr';
import { AreaLine, GroupedColumns, HorizontalBars } from './charts';

const GRANULARITY = { day: 'día', week: 'semana', month: 'mes' };

function bucketLabel(start: string, granularity: Dashboard['granularity']) {
  const [year, month, day] = start.split('-').map(Number);
  const date = new Date(year, month - 1, day);
  if (granularity === 'month') return date.toLocaleDateString('es-MX', { month: 'short', year: '2-digit' });
  const label = date.toLocaleDateString('es-MX', { day: 'numeric', month: 'short' });
  return granularity === 'week' ? `Sem. ${label}` : label;
}

function signed(value: number) {
  return value < 0 ? `−${money(-value)}` : money(value);
}

// Variación contra el periodo anterior; "upIsGood" decide si subir es buena o mala noticia.
function Delta({ current, previous, upIsGood = true }: { current: number; previous: number; upIsGood?: boolean }) {
  if (previous === 0) return <span className="financeDelta">Sin datos del periodo anterior</span>;
  const change = ((current - previous) / Math.abs(previous)) * 100;
  if (Math.abs(change) < 0.5) return <span className="financeDelta">Igual que el periodo anterior</span>;
  const good = change > 0 === upIsGood;
  return (
    <span className={`financeDelta ${good ? 'good' : 'bad'}`}>
      <span aria-hidden="true">{change > 0 ? '▲' : '▼'}</span> {change > 0 ? '+' : ''}{change.toFixed(0)}% vs periodo anterior
    </span>
  );
}

export function FinanceDashboard({ data }: { data: Dashboard }) {
  const { kpis } = data;
  const labels = useMemo(() => data.series.map((row) => bucketLabel(row.start, data.granularity)), [data]);
  const flows = useMemo(() => [
    { label: 'Ingresos', data: data.series.map((row) => row.revenue + row.otherIncome) },
    { label: 'Egresos (honorarios y gastos)', data: data.series.map((row) => row.outflows) },
  ], [data]);
  const cash = useMemo(() => data.series.map((row) => row.cash), [data]);
  const unit = GRANULARITY[data.granularity];
  const empty = data.series.every((row) => !row.revenue && !row.outflows && !row.otherIncome);

  return (
    <div data-testid="finance-dashboard">
      <dl className="financeTiles">
        <div>
          <dt>Ingresos por servicios</dt>
          <dd>{money(kpis.revenue)}</dd>
          <Delta current={kpis.revenue} previous={kpis.previous.revenue} />
        </div>
        <div>
          <dt>Utilidad neta{kpis.netMargin !== null ? ` · margen ${kpis.netMargin}%` : ''}</dt>
          <dd className={kpis.netIncome < 0 ? 'negative' : ''}>{signed(kpis.netIncome)}</dd>
          <Delta current={kpis.netIncome} previous={kpis.previous.netIncome} />
        </div>
        <div>
          <dt>Dinero en cuentas</dt>
          <dd>{signed(kpis.cash)}</dd>
          <Delta current={kpis.cash} previous={kpis.previous.cash} />
        </div>
        <div>
          <dt>Por pagar al equipo</dt>
          <dd>{money(kpis.payables)}</dd>
          <Delta current={kpis.payables} previous={kpis.previous.payables} upIsGood={false} />
        </div>
      </dl>
      <p className="muted financeCompare">
        {kpis.services} {kpis.services === 1 ? 'servicio' : 'servicios'} en el periodo. Se compara contra {formatDate(data.previousFrom)} – {formatDate(data.previousTo)}.
      </p>

      <div className="financeCharts">
        <section className="adminCard financeWide">
          <h2>Ingresos y egresos por {unit}</h2>
          {empty ? <p className="muted">Sin ingresos ni egresos en este periodo.</p> : (
            <GroupedColumns labels={labels} series={flows} label={`Ingresos y egresos por ${unit}; el detalle está en la tabla de abajo.`} />
          )}
        </section>

        <section className="adminCard financeWide">
          <h2>Dinero en cuentas</h2>
          <p className="muted">Caja, banco y Mercado Pago al cierre de cada {unit}.</p>
          <AreaLine labels={labels} data={cash} name="Dinero en cuentas" label={`Dinero en cuentas al cierre de cada ${unit}; el detalle está en la tabla de abajo.`} />
        </section>

        <section className="adminCard">
          <h2>¿A dónde se va el dinero?</h2>
          {data.costBreakdown.length ? (
            <HorizontalBars rows={data.costBreakdown} label={data.costBreakdown.map((row) => `${row.label}: ${money(row.amount)}`).join('; ')} />
          ) : <p className="muted">Sin egresos en este periodo.</p>}
        </section>

        <section className="adminCard">
          <h2>Ingresos por servicio</h2>
          {data.revenueByService.length ? (
            <HorizontalBars rows={data.revenueByService} label={data.revenueByService.map((row) => `${row.label}: ${money(row.amount)}`).join('; ')} />
          ) : <p className="muted">Sin servicios en este periodo.</p>}
          {data.revenueByAccount.length ? (
            <p className="muted financeAccounts">
              Cobrado en: {data.revenueByAccount.map((row) => `${row.label} ${money(row.amount)}`).join(' · ')}
            </p>
          ) : null}
        </section>
      </div>

      <section className="adminCard">
        <h2>Detalle por {unit}</h2>
        <div className="adminTableWrap">
          <table className="adminTable" data-testid="finance-series-table">
            <thead>
              <tr>
                <th>{unit.charAt(0).toUpperCase() + unit.slice(1)}</th>
                <th className="financeAmount">Ingresos</th>
                <th className="financeAmount">Honorarios</th>
                <th className="financeAmount">Gastos</th>
                <th className="financeAmount">Utilidad</th>
                <th className="financeAmount">Dinero al cierre</th>
              </tr>
            </thead>
            <tbody>
              {data.series.map((row, index) => (
                <tr key={row.start}>
                  <td>{labels[index]}</td>
                  <td className="financeAmount">{money(row.revenue + row.otherIncome)}</td>
                  <td className="financeAmount">{money(row.costOfServices)}</td>
                  <td className="financeAmount">{money(row.operatingExpenses)}</td>
                  <td className={`financeAmount${row.netIncome < 0 ? ' negative' : ''}`}>{signed(row.netIncome)}</td>
                  <td className="financeAmount">{signed(row.cash)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
