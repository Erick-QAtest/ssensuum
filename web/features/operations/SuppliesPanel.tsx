'use client';

import { FormEvent, useEffect, useState } from 'react';
import { countOpsSupplies, getOpsSupplies, receiveOpsSupply, saveOpsSupply } from '../../lib/api';
import type { OpsSupply, OpsSupplyInput } from '../../lib/types';

const STATUS = {
  urgente: { label: 'Comprar hoy', badge: 'wait' },
  pedir: { label: 'Pedir', badge: 'wait' },
  sin_contar: { label: 'Falta contar', badge: 'plain' },
  bien: { label: 'Alcanza', badge: 'ok' },
} as const;

const BLANK: OpsSupplyInput = { name: '', unit: '', packSize: 1, dailyUse: 0, leadDays: 2, safetyDays: 3, price: null };

function shortDate(iso: string | null) {
  if (!iso) return '—';
  const [year, month, day] = iso.split('-').map(Number);
  return new Date(year, month - 1, day).toLocaleDateString('es-MX', { weekday: 'short', day: 'numeric', month: 'short' });
}

function amount(value: number | null) {
  return value === null ? '—' : value.toLocaleString('es-MX', { maximumFractionDigits: 1 });
}

// Insumos: cuánto hay, cuánto se gasta al día y cuándo pedir para que nunca se acaben.
export function SuppliesPanel() {
  const [rows, setRows] = useState<OpsSupply[] | null>(null);
  const [counting, setCounting] = useState(false);
  const [counts, setCounts] = useState<Record<string, string>>({});
  const [form, setForm] = useState<OpsSupplyInput>(BLANK);
  const [perPurchaseDays, setPerPurchaseDays] = useState('');
  const [editing, setEditing] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    getOpsSupplies().then(setRows).catch((e: Error) => setError(e.message));
  }, []);

  function run(action: Promise<OpsSupply[]>, after?: () => void) {
    setBusy(true);
    setError('');
    action.then((next) => { setRows(next); after?.(); }).catch((e: Error) => setError(e.message)).finally(() => setBusy(false));
  }

  function saveCount() {
    const values: Record<string, number> = {};
    for (const [id, raw] of Object.entries(counts)) {
      if (raw.trim() === '') continue;
      const value = Number(raw);
      if (!Number.isFinite(value) || value < 0) {
        setError('Las existencias deben ser números de 0 en adelante.');
        return;
      }
      values[id] = value;
    }
    if (!Object.keys(values).length) {
      setError('Escribe al menos una existencia.');
      return;
    }
    run(countOpsSupplies(values), () => { setCounting(false); setCounts({}); });
  }

  function receive(row: OpsSupply) {
    const raw = window.prompt(`¿Cuántos ${row.unit} de ${row.name} llegaron?`, String(row.quantity || row.packSize));
    if (raw === null) return;
    const value = Number(raw);
    if (!Number.isFinite(value) || value <= 0) {
      setError('La cantidad recibida debe ser mayor a 0.');
      return;
    }
    run(receiveOpsSupply(row.id, value));
  }

  function edit(row: OpsSupply) {
    setEditing(row.id);
    setForm({ name: row.name, unit: row.unit, packSize: row.packSize, dailyUse: row.dailyUse, leadDays: row.leadDays, safetyDays: row.safetyDays, price: row.price });
    setPerPurchaseDays(row.dailyUse > 0 ? String(Math.round(row.packSize / row.dailyUse)) : '');
    document.getElementById('supply-form')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function cancel() {
    setEditing(null);
    setForm(BLANK);
    setPerPurchaseDays('');
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    const days = Number(perPurchaseDays);
    if (!Number.isFinite(days) || days <= 0) {
      setError('Escribe cuántos días dura una compra.');
      return;
    }
    run(saveOpsSupply({ ...form, dailyUse: form.packSize / days }, editing ?? undefined), cancel);
  }

  return (
    <>
      <section className="adminCard" data-testid="ops-supplies-panel">
        <div className="adminRow adminRowSpread">
          <h2>Insumos</h2>
          {counting ? (
            <div className="adminRow hrHeadActions">
              <button type="button" className="primaryButton" disabled={busy} onClick={saveCount} data-testid="supplies-save-count">Guardar inventario</button>
              <button type="button" className="secondaryButton" disabled={busy} onClick={() => { setCounting(false); setCounts({}); }}>Cancelar</button>
            </div>
          ) : (
            <button type="button" className="primaryButton" onClick={() => setCounting(true)} data-testid="supplies-count">Contar inventario</button>
          )}
        </div>
        <p className="muted">
          El sistema descuenta el consumo diario desde el último conteo. Si al llegar el pedido de la semana siguiente quedaría menos que el margen de seguridad,
          lo marca para el pedido del miércoles; si ni así alcanza, para comprar hoy. Cada inventario corrige el consumo con lo que de verdad se gastó.
        </p>
        {error ? <div className="errorBox" role="alert">{error}</div> : null}
        {rows === null && !error ? <p className="muted">Cargando…</p> : null}
        {rows?.length ? (
          <div className="adminTableWrap">
            <table className="adminTable">
              <thead><tr><th>Insumo</th><th>Hay</th><th>Gasto por día</th><th>Alcanza hasta</th><th>Estado</th><th></th></tr></thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.id} data-testid="supply-row">
                    <td>{row.name}<span className="adminSub">Conteo: {row.countedOn ? `${amount(row.countedStock)} el ${shortDate(row.countedOn)}` : 'sin contar'}</span></td>
                    <td>
                      {counting ? (
                        <input
                          className="opsCountInput"
                          type="number"
                          inputMode="decimal"
                          min={0}
                          step="any"
                          value={counts[row.id] ?? ''}
                          onChange={(event) => setCounts((current) => ({ ...current, [row.id]: event.target.value }))}
                          aria-label={`Existencia de ${row.name} en ${row.unit}`}
                        />
                      ) : null}
                      {counting ? ` ${row.unit}` : `${amount(row.estimate)} ${row.unit}`}
                    </td>
                    <td>{amount(row.dailyUse)} {row.unit}<span className="adminSub">1 {row.unit} cada {row.dailyUse > 0 ? Math.round(1 / row.dailyUse) : '—'} días</span></td>
                    <td>{shortDate(row.runsOutOn)}</td>
                    <td>
                      <span className={`statusBadge ${STATUS[row.status].badge}`}>{STATUS[row.status].label}</span>
                      {row.status === 'pedir' || row.status === 'urgente' ? (
                        <span className="adminSub">{row.quantity} {row.unit}{row.status === 'pedir' ? ` el ${shortDate(row.orderOn)}` : ''}</span>
                      ) : null}
                    </td>
                    <td className="recordActions">
                      <button type="button" className="hrLink" disabled={busy || row.countedStock === null} onClick={() => receive(row)}>Recibí</button>
                      <button type="button" className="hrLink marketingGap" onClick={() => edit(row)}>Editar</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>

      <form id="supply-form" className="adminCard recordForm" onSubmit={submit} data-testid="supply-form">
        <h2>{editing ? 'Editar insumo' : 'Agregar insumo'}</h2>
        <div className="recordGrid">
          <label>Nombre<input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} maxLength={80} required /></label>
          <label>Unidad<input value={form.unit} onChange={(event) => setForm({ ...form, unit: event.target.value })} maxLength={30} placeholder="bote, caja, litro…" required /></label>
          <label>Cantidad por compra<input type="number" min={0.1} step="any" value={form.packSize} onChange={(event) => setForm({ ...form, packSize: Number(event.target.value) })} required /></label>
          <label>Días que dura esa compra<input type="number" min={1} step={1} value={perPurchaseDays} onChange={(event) => setPerPurchaseDays(event.target.value)} required /></label>
          <label>Días de entrega<input type="number" min={0} max={60} step={1} value={form.leadDays} onChange={(event) => setForm({ ...form, leadDays: Number(event.target.value) })} required /></label>
          <label>Días de margen<input type="number" min={0} max={60} step={1} value={form.safetyDays} onChange={(event) => setForm({ ...form, safetyDays: Number(event.target.value) })} required /></label>
          <label>Precio por compra<input type="number" min={0} step={1} value={form.price ?? ''} onChange={(event) => setForm({ ...form, price: event.target.value === '' ? null : Number(event.target.value) })} placeholder="Opcional" /></label>
        </div>
        <div className="adminRow">
          <button type="submit" className="primaryButton" disabled={busy}>{editing ? 'Guardar cambios' : 'Agregar'}</button>
          {editing ? <button type="button" className="secondaryButton" onClick={cancel}>Cancelar</button> : null}
        </div>
      </form>
    </>
  );
}
