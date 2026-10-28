'use client';

import { FormEvent, useEffect, useState } from 'react';
import { saveStaffPhoto, saveStaffProfile } from '../../lib/api';
import type { StaffMember } from '../../lib/types';
import { PhotoCapture } from './PhotoCapture';

type Props = {
  member: StaffMember;
  onSaved: (member: StaffMember) => void;
  onCancel: () => void;
};

export function StaffForm({ member, onSaved, onCancel }: Props) {
  const [photo, setPhoto] = useState<Blob | null>(null);
  const [name, setName] = useState('');
  const [strengths, setStrengths] = useState('');
  const [bio, setBio] = useState('');
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
    setName(member.name);
    setStrengths(member.strengths);
    setBio(member.bio ?? '');
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
    // La foto va primero: si falla, el expediente no se guarda a medias.
    (photo ? saveStaffPhoto(member.id, photo) : Promise.resolve(member))
      .then(() => saveStaffProfile(member.id, { name, strengths, bio, fullName, phone, email, birthday: birthday || null, hiredOn: hiredOn || null, emergencyContact, notes }))
      .then(onSaved)
      .catch((e: Error) => setError(e.message))
      .finally(() => setSaving(false));
  }

  return (
    <section className="adminCard" data-testid="staff-form">
      <h2>Expediente de {member.name}</h2>
      <form className="recordForm" onSubmit={submit}>
        <h3 className="hrSubhead">Foto</h3>
        <PhotoCapture key={member.id} onChange={setPhoto} currentUrl={member.photoUrl} />
        <h3 className="hrSubhead">Perfil en el sitio</h3>
        <div className="recordGrid">
          <label>Nombre en el sitio<input value={name} onChange={(event) => setName(event.target.value)} autoComplete="off" required /></label>
          <label>Fortalezas<input value={strengths} onChange={(event) => setStrengths(event.target.value)} placeholder="Separadas por comas" /></label>
        </div>
        <label className="recordNotes">Descripción<textarea rows={3} value={bio} onChange={(event) => setBio(event.target.value)} /></label>
        <h3 className="hrSubhead">Expediente</h3>
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
