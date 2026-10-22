'use client';

import { FormEvent, WheelEvent, useCallback, useEffect, useState } from 'react';
import { createRecurringExpense, endRecurringExpense, getRecurringExpenses } from '../../lib/api';
import { money } from '../../lib/format';
import type { FinanceMeta, RecurringExpense } from '../../lib/types';

function monthLabel(month: string) {
  const [year, number] = month.split('-').map(Number);
  return new Date(year, number - 1, 1).toLocaleDateString('es-MX', { month: 'long', year: 'numeric' });
}

function currentMonth() {
  const today = new Date();
  return `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`;
}

function keepAmount(event: WheelEvent<HTMLInputElement>) {
  event.currentTarget.blur();
}

export function RecurringExpenses({ meta, onChanged }: { meta: FinanceMeta; onChanged: () => void }) {
  const [items, setItems] = useState<RecurringExpense[] | null>(null);
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('renta');
  const [amount, setAmount] = useState('');
  const [account, setAccount] = useState('banco');
  const [day, setDay] = useState('1');
  const [startMonth, setStartMonth] = useState(currentMonth);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(() => getRecurringExpenses().then(setItems).catch((e: Error) => setError(e.message)), []);
  useEffect(() => { load(); }, [load]);

  function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError('');
    createRecurringExpense({ description, category, amount: Math.round(Number(amount || 0)), account, dayOfMonth: Number(day), startMonth })
      .then(() => { setDescription(''); setAmount(''); load(); onChanged(); })
      .catch((e: Error) => setError(e.message))
      .finally(() => setSaving(false));
  }

  function end(item: RecurringExpense) {
    const last = currentMonth();
    if (!window.confirm(`¿Dar de baja “${item.description}”? Se conserva hasta ${monthLabel(last)} y deja de registrarse después.`)) return;
    endRecurringExpense(item.id, last).then(() => { load(); onChanged(); }).catch((e: Error) => setError(e.message));
  }

  const active = items?.filter((item) => !item.endMonth || item.endMonth >= currentMonth()) ?? [];
  const monthly = active.reduce((sum, item) => sum + item.amount, 0);

  return (
    <section className="adminCard" data-testid="recurring-expenses">
      <h2>Gastos fijos</h2>
      <p className="muted">Se registran solos cada mes en la fecha indicada; no hace falta capturarlos.{monthly ? ` Total mensual vigente: ${money(monthly)}.` : ''}</p>

      {items && items.length > 0 ? (
        <div className="adminTableWrap">
          <table className="adminTable">
            <thead><tr><th>Gasto</th><th>Cada mes</th><th>Cuenta</th><th className="financeAmount">Importe</th><th></th></tr></thead>
            <tbody>
              {items.map((item) => (
                  <tr key={item.id} data-testid="recurring-row">
                    <td>{item.description}<span className="adminSub">{item.categoryLabel}</span></td>
                    <td>
                      Día {item.dayOfMonth}
                      <span className="adminSub">
                        Desde {monthLabel(item.startMonth)}{item.endMonth ? ` hasta ${monthLabel(item.endMonth)}` : ''}
                      </span>
                    </td>
                    <td>{item.accountLabel}</td>
                    <td className="financeAmount">{money(item.amount)}</td>
                    <td className="recordActions">
                      {item.endMonth ? <span className="statusBadge wait">De baja</span> : (
                        <button type="button" className="linkButton" onClick={() => end(item)}>Dar de baja</button>
                      )}
                    </td>
                  </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      <form className="recordForm" onSubmit={submit}>
        <div className="recordGrid">
          <label>Descripción<input value={description} onChange={(event) => setDescription(event.target.value)} maxLength={200} placeholder="Ej. Renta del local" /></label>
          <label>Categoría
            <select value={category} onChange={(event) => setCategory(event.target.value)}>
              {meta.expenseCategories.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
          </label>
          <label>Importe mensual (MXN)<input type="number" inputMode="numeric" min="1" step="1" value={amount} onWheel={keepAmount} onChange={(event) => setAmount(event.target.value)} /></label>
          <label>Pagado desde
            <select value={account} onChange={(event) => setAccount(event.target.value)}>
              {meta.accounts.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
          </label>
          <label>Día de pago
            <select value={day} onChange={(event) => setDay(event.target.value)}>
              {Array.from({ length: 31 }, (_, index) => String(index + 1)).map((value) => (
                <option key={value} value={value}>{value === '31' ? '31 o último día del mes' : value}</option>
              ))}
            </select>
          </label>
          <label>Desde el mes<input type="month" value={startMonth} onChange={(event) => setStartMonth(event.target.value)} required /></label>
        </div>
        {error ? <div className="errorBox" role="alert">{error}</div> : null}
        <div className="adminRow">
          <button type="submit" className="primaryButton" disabled={!description.trim() || !(Number(amount) > 0) || !startMonth || saving}>
            {saving ? 'Guardando…' : 'Agregar gasto fijo'}
          </button>
        </div>
      </form>
    </section>
  );
}
