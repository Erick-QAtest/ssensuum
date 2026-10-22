'use client';

import { FormEvent, WheelEvent, useState } from 'react';
import { createFinanceMovement } from '../../lib/api';
import type { FinanceMeta } from '../../lib/types';
import { localIsoDate } from '../booking/dates';

// De qué cuenta sale o a cuál entra el dinero, según el tipo de movimiento.
const ACCOUNT_LABEL: Record<string, string> = {
  gasto: 'Pagado desde',
  retiro: 'Sale de',
  pago_prestamo: 'Pagado desde',
  activo: 'Pagado desde',
  traspaso: 'Sale de',
};

const HINTS: Record<string, string> = {
  saldo_inicial: 'Lo que había en cada cuenta al empezar a usar Finanzas. Captura uno por cuenta.',
  aportacion: 'Dinero que el dueño mete al negocio.',
  retiro: 'Dinero que el dueño saca del negocio para sí.',
  activo: 'Compra de camillas, muebles o equipo que dura más de un año.',
  ingreso: 'Ingresos que no vienen del registro de servicios, por ejemplo la limpieza que un masajista paga aparte.',
  traspaso: 'Mover dinero entre tus cuentas, por ejemplo depositar el efectivo de caja al banco.',
};

function keepAmount(event: WheelEvent<HTMLInputElement>) {
  event.currentTarget.blur();
}

export function MovementForm({ meta, onSaved }: { meta: FinanceMeta; onSaved: () => void }) {
  const [kind, setKind] = useState('gasto');
  const [day, setDay] = useState(() => localIsoDate(new Date()));
  const [category, setCategory] = useState('');
  const [description, setDescription] = useState('');
  const [amount, setAmount] = useState('');
  const [account, setAccount] = useState('banco');
  const [toAccount, setToAccount] = useState('caja');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const categories = kind === 'gasto' ? meta.expenseCategories : kind === 'ingreso' ? meta.incomeCategories : null;

  function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError('');
    setNotice('');
    createFinanceMovement({
      day,
      kind,
      category: categories ? category : null,
      description,
      amount: Math.round(Number(amount || 0)),
      account,
      toAccount: kind === 'traspaso' ? toAccount : null,
    })
      .then((movement) => {
        setNotice(`Se guardó: ${movement.kindLabel.toLowerCase()} de ${movement.description}.`);
        setDescription('');
        setAmount('');
        onSaved();
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setSaving(false));
  }

  const canSave = description.trim() && Number(amount) > 0 && (!categories || category) && !saving;

  return (
    <form className="recordForm" onSubmit={submit} data-testid="finance-movement-form">
      <div className="recordGrid">
        <label>Tipo
          <select value={kind} onChange={(event) => { setKind(event.target.value); setCategory(''); }}>
            {meta.kinds.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
        </label>
        <label>Fecha<input type="date" value={day} onChange={(event) => setDay(event.target.value)} required /></label>
        {categories ? (
          <label>Categoría
            <select value={category} onChange={(event) => setCategory(event.target.value)} required>
              <option value="">Elige…</option>
              {categories.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
          </label>
        ) : null}
        <label>Descripción<input value={description} onChange={(event) => setDescription(event.target.value)} maxLength={200} placeholder="Ej. Renta de noviembre" /></label>
        <label>Importe (MXN)<input type="number" inputMode="numeric" min="1" step="1" value={amount} onWheel={keepAmount} onChange={(event) => setAmount(event.target.value)} /></label>
        <label>{ACCOUNT_LABEL[kind] ?? 'Entra a'}
          <select value={account} onChange={(event) => setAccount(event.target.value)}>
            {meta.accounts.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
        </label>
        {kind === 'traspaso' ? (
          <label>Entra a
            <select value={toAccount} onChange={(event) => setToAccount(event.target.value)}>
              {meta.accounts.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
          </label>
        ) : null}
      </div>
      {HINTS[kind] ? <p className="muted">{HINTS[kind]}</p> : null}
      {error ? <div className="errorBox" role="alert">{error}</div> : null}
      {notice ? <div className="successBox" role="status">{notice}</div> : null}
      <div className="adminRow">
        <button type="submit" className="primaryButton" disabled={!canSave}>{saving ? 'Guardando…' : 'Guardar movimiento'}</button>
      </div>
    </form>
  );
}
