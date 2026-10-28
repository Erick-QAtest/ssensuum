'use client';

import { FormEvent, useState } from 'react';
import { hireStaff } from '../../lib/api';
import type { HrDocumentCategory, StaffMember } from '../../lib/types';
import { PhotoCapture } from './PhotoCapture';
import { todayInput } from './hr';

type Props = {
  onHired: (member: StaffMember) => void;
  onCapture: (member: StaffMember, category: HrDocumentCategory) => void;
  onClose: () => void;
};

const STEPS = ['Foto', 'Perfil en el sitio', 'Expediente', 'Confirmar'];

// Alta paso a paso. Nada se guarda hasta confirmar, para no dejar masajistas a medias en el sitio.
export function HireWizard({ onHired, onCapture, onClose }: Props) {
  const [step, setStep] = useState(0);
  const [photo, setPhoto] = useState<Blob | null>(null);
  const [preview, setPreview] = useState('');
  const [name, setName] = useState('');
  const [strengths, setStrengths] = useState('');
  const [bio, setBio] = useState('');
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [birthday, setBirthday] = useState('');
  const [hiredOn, setHiredOn] = useState(todayInput);
  const [emergencyContact, setEmergencyContact] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [hired, setHired] = useState<StaffMember | null>(null);

  const ready = [Boolean(photo), name.trim().length > 0 && strengths.trim().length > 0 && bio.trim().length > 0, fullName.trim().length > 0 && phone.trim().length > 0, true];

  function next(event: FormEvent) {
    event.preventDefault();
    if (!ready[step]) return;
    setError('');
    if (step === 0 && photo) setPreview(URL.createObjectURL(photo));
    if (step < STEPS.length - 1) {
      setStep(step + 1);
      return;
    }
    setSaving(true);
    hireStaff({ name, strengths, bio, fullName, phone, email, birthday: birthday || null, hiredOn: hiredOn || null, emergencyContact, notes: '' }, photo as Blob)
      .then((member) => { setHired(member); onHired(member); })
      .catch((e: Error) => setError(e.message))
      .finally(() => setSaving(false));
  }

  if (hired) {
    return (
      <section className="adminCard" data-testid="hire-done">
        <h2>{hired.name} ya es parte del equipo</h2>
        <p className="muted">Ya aparece en el sitio y en las reservas, y con su foto en este tablero.</p>
        <h3 className="hrSubhead">Último paso: su documentación</h3>
        <p className="muted">Imprime los formatos para firmar, fírmalos con {hired.name} y captura cada uno:</p>
        <ul className="hrTemplates">
          {hired.missingDocuments.map((missing) => (
            <li key={missing.category}>
              <strong>{missing.label}</strong>
              <button type="button" className="secondaryButton" onClick={() => onCapture(hired, missing.category)}>Capturar</button>
            </li>
          ))}
        </ul>
        <div className="adminRow">
          <button type="button" className="primaryButton" onClick={onClose}>Terminar</button>
        </div>
      </section>
    );
  }

  return (
    <section className="adminCard" data-testid="hire-wizard">
      <div className="adminRow adminRowSpread">
        <h2>Dar de alta masajista</h2>
        <button type="button" className="hrLink" onClick={onClose}>Cancelar alta</button>
      </div>
      <ol className="hrSteps" aria-label="Pasos del alta">
        {STEPS.map((label, index) => (
          <li key={label} className={index === step ? 'current' : index < step ? 'done' : ''} aria-current={index === step ? 'step' : undefined}>
            <span>{index + 1}</span>{label}
          </li>
        ))}
      </ol>

      <form className="recordForm" onSubmit={next}>
        <div hidden={step !== 0}>
          <p className="muted">Tómale la foto aquí mismo o sube una. Es la que verán los clientes en el sitio y la que aparece en este tablero.</p>
          <PhotoCapture onChange={setPhoto} />
        </div>

        {step === 1 ? (
          <>
            <p className="muted">Así lo verán los clientes en la sección de equipo del sitio.</p>
            <div className="recordGrid">
              <label>Nombre en el sitio<input value={name} onChange={(event) => setName(event.target.value)} placeholder="Ej. Kevin" autoComplete="off" required /></label>
              <label>Fortalezas<input value={strengths} onChange={(event) => setStrengths(event.target.value)} placeholder="Tres palabras separadas por comas" required /></label>
            </div>
            <label className="recordNotes">Descripción<textarea rows={4} value={bio} onChange={(event) => setBio(event.target.value)} placeholder="Dos o tres frases sobre su trato y el tipo de sesión que da." required /></label>
          </>
        ) : null}

        {step === 2 ? (
          <>
            <p className="muted">Datos internos: solo los ve Recursos humanos.</p>
            <div className="recordGrid">
              <label>Nombre completo<input value={fullName} onChange={(event) => setFullName(event.target.value)} autoComplete="off" required /></label>
              <label>Teléfono<input type="tel" inputMode="tel" value={phone} onChange={(event) => setPhone(event.target.value)} placeholder="10 dígitos" required /></label>
              <label>Correo<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} /></label>
              <label>Contacto de emergencia<input value={emergencyContact} onChange={(event) => setEmergencyContact(event.target.value)} placeholder="Nombre y teléfono" /></label>
              <label>Fecha de ingreso<input type="date" value={hiredOn} onChange={(event) => setHiredOn(event.target.value)} /></label>
              <label>Cumpleaños<input type="date" value={birthday} onChange={(event) => setBirthday(event.target.value)} /></label>
            </div>
          </>
        ) : null}

        {step === 3 ? (
          <div className="hrReview">
            {preview ? <img src={preview} alt={`Foto de ${name}`} /> : null}
            <div>
              <h3>{name}</h3>
              <p className="adminSub">{strengths}</p>
              <p>{bio}</p>
              <p className="adminSub">{fullName} · {phone}{email ? ` · ${email}` : ''}</p>
              <p className="muted">Al confirmar aparece de inmediato en el sitio y ya se le pueden hacer reservas.</p>
            </div>
          </div>
        ) : null}

        {error ? <div className="errorBox" role="alert">{error}</div> : null}
        <div className="adminRow">
          {step > 0 ? <button type="button" className="secondaryButton" disabled={saving} onClick={() => setStep(step - 1)}>Atrás</button> : null}
          <button type="submit" className="primaryButton" disabled={!ready[step] || saving} data-testid="hire-next">
            {step === STEPS.length - 1 ? (saving ? 'Dando de alta…' : 'Confirmar alta') : 'Siguiente'}
          </button>
        </div>
      </form>
    </section>
  );
}
