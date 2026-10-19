'use client';

import { FormEvent, WheelEvent, useEffect, useMemo, useState } from 'react';
import { searchCustomers, saveServiceRecord } from '../../lib/api';
import type { PaymentMethod, Service, ServiceRecord, Therapist } from '../../lib/types';
import { PAYMENT_METHODS, localDateTimeInput } from './records';

type Props = {
  services: Service[];
  therapists: Therapist[];
  editing: ServiceRecord | null;
  onSaved: (record: ServiceRecord) => void;
  onCancel: () => void;
};

// Evita que la rueda del mouse cambie un monto mientras se recorre la página.
function keepAmount(event: WheelEvent<HTMLInputElement>) {
  event.currentTarget.blur();
}

function digits(value: string) {
  return value.replace(/\D/g, '').slice(-10);
}

export function RecordForm({ services, therapists, editing, onSaved, onCancel }: Props) {
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [serviceId, setServiceId] = useState('');
  const [therapistIds, setTherapistIds] = useState<string[]>([]);
  const [paidAt, setPaidAt] = useState(() => localDateTimeInput(new Date().toISOString()));
  const [amount, setAmount] = useState('');
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('efectivo');
  const [tips, setTips] = useState<Record<string, string>>({});
  const [tipMethod, setTipMethod] = useState<PaymentMethod>('efectivo');
  const [notes, setNotes] = useState('');
  const [knownCustomer, setKnownCustomer] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  function reset() {
    setName(''); setPhone(''); setServiceId(''); setTherapistIds([]);
    setPaidAt(localDateTimeInput(new Date().toISOString()));
    setAmount(''); setPaymentMethod('efectivo'); setTips({}); setTipMethod('efectivo'); setNotes('');
    setError('');
  }

  // Al terminar o cancelar una edición, el formulario vuelve a quedar en blanco.
  useEffect(() => {
    if (!editing) {
      reset();
      return;
    }
    setName(editing.customerName);
    setPhone(editing.customerPhone);
    setServiceId(editing.serviceId);
    setTherapistIds(editing.therapistIds);
    setPaidAt(localDateTimeInput(editing.paidAt));
    setAmount(String(editing.amount));
    setPaymentMethod(editing.paymentMethod);
    setTips(Object.fromEntries(editing.tips.map((tip) => [tip.therapistId, String(tip.amount)])));
    setTipMethod(editing.tipMethod ?? 'efectivo');
    setNotes(editing.notes ?? '');
    setError('');
  }, [editing]);

  // Al escribir un teléfono ya registrado se completa el nombre del cliente.
  useEffect(() => {
    const number = digits(phone);
    setKnownCustomer('');
    if (number.length !== 10) return;
    let active = true;
    searchCustomers(number)
      .then((rows) => {
        const match = rows.find((row) => row.phone === number);
        if (!active || !match) return;
        const fullName = `${match.firstName} ${match.lastName}`.trim();
        setKnownCustomer(fullName);
        setName((current) => current.trim() ? current : fullName);
      })
      .catch(() => null);
    return () => { active = false; };
  }, [phone]);

  const service = services.find((row) => row.id === serviceId);
  const byCategory = useMemo(() => {
    const groups = new Map<string, Service[]>();
    for (const row of services) groups.set(row.category, [...(groups.get(row.category) ?? []), row]);
    return [...groups.entries()];
  }, [services]);

  function chooseService(id: string) {
    setServiceId(id);
    const next = services.find((row) => row.id === id);
    if (next && !editing) setAmount(String(next.publicPrice));
  }

  function toggleTherapist(id: string) {
    setTherapistIds((current) => current.includes(id) ? current.filter((value) => value !== id) : [...current, id]);
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError('');
    const tipEntries = therapistIds
      .map((therapistId) => ({ therapistId, amount: Math.max(0, Math.round(Number(tips[therapistId] || 0))) }))
      .filter((tip) => tip.amount > 0);
    try {
      const saved = await saveServiceRecord({
        customerName: name,
        customerPhone: phone,
        serviceId,
        therapistIds,
        paidAt,
        amount: Math.round(Number(amount || 0)),
        paymentMethod,
        tips: tipEntries,
        tipMethod: tipEntries.length ? tipMethod : null,
        notes: notes.trim() || null,
      }, editing?.id);
      reset();
      onSaved(saved);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  }

  const needed = service?.therapistsRequired ?? 1;
  const canSave = name.trim() && digits(phone).length === 10 && serviceId && therapistIds.length > 0 && amount !== '' && !saving;
  const selectedTherapists = therapists.filter((row) => therapistIds.includes(row.id));

  return (
    <form className="adminCard recordForm" onSubmit={submit} data-testid="record-form">
      <h2>{editing ? 'Editar registro' : 'Nuevo registro'}</h2>

      <div className="recordGrid">
        <label>Nombre del cliente
          <input value={name} onChange={(event) => setName(event.target.value)} autoComplete="off" required data-testid="record-name" />
        </label>
        <label>Celular
          <input value={phone} onChange={(event) => setPhone(event.target.value)} inputMode="tel" placeholder="10 dígitos" required data-testid="record-phone" />
          {knownCustomer ? <small className="adminSub">Cliente registrado: {knownCustomer}</small> : null}
        </label>
        <label>Servicio
          <select value={serviceId} onChange={(event) => chooseService(event.target.value)} required data-testid="record-service">
            <option value="" disabled>Elige un servicio</option>
            {byCategory.map(([category, rows]) => (
              <optgroup key={category} label={category}>
                {rows.map((row) => <option key={row.id} value={row.id}>{row.name}</option>)}
              </optgroup>
            ))}
          </select>
        </label>
        <label>Fecha y hora del cobro
          <input type="datetime-local" value={paidAt} onChange={(event) => setPaidAt(event.target.value)} required data-testid="record-paid-at" />
        </label>
      </div>

      <fieldset className="recordFieldset">
        <legend>Terapeutas {needed > 1 ? <small className="muted">· este servicio lleva {needed}</small> : null}</legend>
        <div className="recordChips">
          {therapists.map((row) => (
            <button
              type="button"
              key={row.id}
              className={`secondaryButton ${therapistIds.includes(row.id) ? 'selected' : ''}`}
              aria-pressed={therapistIds.includes(row.id)}
              onClick={() => toggleTherapist(row.id)}
            >
              {row.name}
            </button>
          ))}
        </div>
      </fieldset>

      <div className="recordGrid">
        <label>Monto cobrado (MXN)
          <input type="number" min={0} step={1} onWheel={keepAmount} value={amount} onChange={(event) => setAmount(event.target.value)} required data-testid="record-amount" />
        </label>
        <label>Forma de pago
          <select value={paymentMethod} onChange={(event) => setPaymentMethod(event.target.value as PaymentMethod)}>
            {PAYMENT_METHODS.map((method) => <option key={method.id} value={method.id}>{method.label}</option>)}
          </select>
        </label>
      </div>

      <section className="recordTips" aria-label="Propinas">
        <h3>Propinas</h3>
        {selectedTherapists.length === 0 ? <p className="muted">Elige primero a los terapeutas que atendieron.</p> : (
          <div className="recordGrid">
            {selectedTherapists.map((row) => (
              <label key={row.id}>Para {row.name}
                <input
                  type="number"
                  min={0}
                  step={1}
                  onWheel={keepAmount}
                  placeholder="0"
                  value={tips[row.id] ?? ''}
                  onChange={(event) => setTips((current) => ({ ...current, [row.id]: event.target.value }))}
                  data-testid="record-tip"
                />
              </label>
            ))}
            <label>Propina pagada con
              <select value={tipMethod} onChange={(event) => setTipMethod(event.target.value as PaymentMethod)}>
                {PAYMENT_METHODS.map((method) => <option key={method.id} value={method.id}>{method.label}</option>)}
              </select>
            </label>
          </div>
        )}
      </section>

      <label className="recordNotes">Notas
        <input value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="Opcional" />
      </label>

      {error ? <div className="errorBox" role="alert">{error}</div> : null}

      <div className="adminRow">
        <button type="submit" className="primaryButton" disabled={!canSave} data-testid="record-save">
          {saving ? 'Guardando…' : editing ? 'Guardar cambios' : 'Registrar'}
        </button>
        {editing ? <button type="button" className="secondaryButton" onClick={onCancel}>Cancelar</button> : null}
      </div>
    </form>
  );
}
