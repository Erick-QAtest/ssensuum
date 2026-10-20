'use client';

import { FormEvent, useEffect, useState } from 'react';
import { saveStaffProfile } from '../../lib/api';
import type { StaffMember } from '../../lib/types';

type Props = {
  member: StaffMember;
  onSaved: (member: StaffMember) => void;
  onCancel: () => void;
};

export function StaffForm({ member, onSaved, onCancel }: Props) {
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [birthday, setBirthday] = useState('');
  const [hiredOn, setHiredOn] = useState('');
  const [emergencyContact, setEmergencyContact] = useState('');
  const [notes, setNotes] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setFullName(member.fullName ?? '');
    setPhone(member.phone ?? '');
    setEmail(member.email ?? '');
    setBirthday(member.birthday ?? '');
    setHiredOn(member.hiredOn ?? '');
    setEmergencyContact(member.emergencyContact ?? '');
    setNotes(member.notes ?? '');
    setError('');
  }, [member]);

  function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError('');
    saveStaffProfile(member.id, { fullName, phone, email, birthday: birthday || null, hiredOn: hiredOn || null, emergencyContact, notes })
      .then(onSaved)
      .catch((e: Error) => setError(e.message))
      .finally(() => setSaving(false));
  }

  return (
    <section className="adminCard" data-testid="staff-form">
      <h2>Expediente de {member.name}</h2>
      <form className="recordForm" onSubmit={submit}>
        <div className="recordGrid">
          <label>Nombre completo<input value={fullName} onChange={(event) => setFullName(event.target.value)} autoComplete="off" /></label>
          <label>Teléfono<input type="tel" inputMode="tel" value={phone} onChange={(event) => setPhone(event.target.value)} placeholder="10 dígitos" /></label>
          <label>Correo<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} /></label>
          <label>Contacto de emergencia<input value={emergencyContact} onChange={(event) => setEmergencyContact(event.target.value)} placeholder="Nombre y teléfono" /></label>
          <label>Fecha de ingreso<input type="date" value={hiredOn} onChange={(event) => setHiredOn(event.target.value)} /></label>
          <label>Cumpleaños<input type="date" value={birthday} onChange={(event) => setBirthday(event.target.value)} /></label>
        </div>
        <label className="recordNotes">Notas<input value={notes} onChange={(event) => setNotes(event.target.value)} /></label>
        {error ? <div className="errorBox" role="alert">{error}</div> : null}
        <div className="adminRow">
          <button type="submit" className="primaryButton" disabled={saving}>{saving ? 'Guardando…' : 'Guardar expediente'}</button>
          <button type="button" className="secondaryButton" disabled={saving} onClick={onCancel}>Cancelar</button>
        </div>
      </form>
    </section>
  );
}
