'use client';

import { useEffect, useRef, useState } from 'react';
import { CloseIcon } from '../../components/icons';
import { ApiError, getFeedbackContext, sendFeedback, track } from '../../lib/api';
import type { FeedbackContext } from '../../lib/types';
import { whatsappUrl } from '../../lib/whatsapp';
import { StarRating } from './StarRating';

// Se abre desde el WhatsApp que recepción manda desde Registro de servicios: /?calificar=<id del servicio registrado>.
export const FEEDBACK_PARAM = 'calificar';

type Step = 'form' | 'thanks' | 'answered';

function rebookHref(context: FeedbackContext) {
  const params = new URLSearchParams({ service: context.serviceId });
  if (context.therapistIds.length === 1) params.set('therapist', context.therapistIds[0]);
  return `/reservar?${params.toString()}`;
}

export function FeedbackModal() {
  const [context, setContext] = useState<FeedbackContext | null>(null);
  const [step, setStep] = useState<Step>('form');
  const [massage, setMassage] = useState(0);
  const [cleanliness, setCleanliness] = useState(0);
  const [therapistStars, setTherapistStars] = useState<Record<string, number>>({});
  const [comment, setComment] = useState('');
  const [email, setEmail] = useState('');
  const [birthday, setBirthday] = useState('');
  const [source, setSource] = useState('');
  // Marcada de inicio; el cliente la puede quitar (aviso de privacidad: "No deseo recibir promociones").
  const [whatsappOptIn, setWhatsappOptIn] = useState(true);
  const [error, setError] = useState('');
  const [sending, setSending] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const id = new URLSearchParams(window.location.search).get(FEEDBACK_PARAM);
    if (!id) return;
    getFeedbackContext(id)
      .then((row) => { setContext(row); setStep(row.answered ? 'answered' : 'form'); })
      // Enlace inválido: la home se ve normal, sin pop up.
      .catch(() => null);
  }, []);

  const open = context !== null;

  useEffect(() => {
    if (!open) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    panelRef.current?.focus();
    const onKey = (event: KeyboardEvent) => { if (event.key === 'Escape') close(); };
    window.addEventListener('keydown', onKey);
    return () => { document.body.style.overflow = previous; window.removeEventListener('keydown', onKey); };
  }, [open]);

  function close() {
    setContext(null);
    const url = new URL(window.location.href);
    url.searchParams.delete(FEEDBACK_PARAM);
    window.history.replaceState(null, '', url.pathname + url.search + url.hash);
  }

  function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!context) return;
    const therapistRatings = context.therapistIds.map((id) => ({ therapistId: id, rating: therapistStars[id] ?? 0 }));
    if (!massage || !cleanliness || therapistRatings.some((row) => !row.rating)) {
      setError('Califica el masaje, a tu masajista y la limpieza con estrellas.');
      return;
    }
    setSending(true);
    setError('');
    sendFeedback(context.visitId, {
      massageRating: massage,
      cleanlinessRating: cleanliness,
      therapistRatings,
      comment,
      email: context.asks.email && email.trim() ? email.trim() : undefined,
      birthday: context.asks.birthday && birthday ? birthday : undefined,
      source: context.asks.source && source ? source : undefined,
      whatsappOptIn,
    })
      .then(() => setStep('thanks'))
      .catch((e: unknown) => {
        if (e instanceof ApiError && e.status === 409) setStep('answered');
        else setError(e instanceof Error ? e.message : 'No pudimos guardar tu calificación');
      })
      .finally(() => setSending(false));
  }

  if (!context) return null;

  const therapist = context.therapistNames.join(' y ');
  const ratedTherapists = context.therapistIds.map((id) => therapistStars[id] ?? 0);
  const happy = massage >= 4 && cleanliness >= 4 && ratedTherapists.every((value) => value >= 4);
  const asksData = context.asks.email || context.asks.birthday || context.asks.source;
  const clearError = () => setError('');

  return (
    <div className="feedbackOverlay" onClick={(event) => { if (event.target === event.currentTarget) close(); }}>
      <div className="feedbackPanel" role="dialog" aria-modal="true" aria-labelledby="feedback-title" tabIndex={-1} ref={panelRef}>
        <button type="button" className="feedbackClose" aria-label="Cerrar" onClick={close}><CloseIcon /></button>

        {step === 'form' ? (
          <form onSubmit={submit} noValidate>
            <span className="kicker">Tu opinión</span>
            <h2 id="feedback-title">{context.firstName ? `${context.firstName}, ¿cómo te fue?` : '¿Cómo te fue?'}</h2>
            <p className="feedbackLead">
              {context.serviceName}{therapist ? ` con ${therapist}` : ''}. Toma menos de un minuto y lo lee el equipo.
            </p>
            <StarRating name="massage" label="¿Cómo calificarías tu masaje?" value={massage} onChange={(value) => { setMassage(value); clearError(); }} />
            {context.therapistIds.map((id, index) => (
              <StarRating
                key={id}
                name={`therapist-${id}`}
                label={`¿Cómo te atendió ${context.therapistNames[index]}?`}
                value={therapistStars[id] ?? 0}
                onChange={(value) => { setTherapistStars((current) => ({ ...current, [id]: value })); clearError(); }}
              />
            ))}
            <StarRating name="cleanliness" label="¿Y la limpieza de la cabina?" value={cleanliness} onChange={(value) => { setCleanliness(value); clearError(); }} />
            <label className="feedbackComment">
              <span>¿Cómo mejoramos tu próxima visita? <em>(opcional)</em></span>
              <textarea value={comment} maxLength={1000} rows={3} placeholder="Música, temperatura, presión, toallas…" onChange={(event) => setComment(event.target.value)} />
            </label>
            {asksData ? (
              <fieldset className="feedbackData">
                <legend>Para conocerte mejor <em>(opcional)</em></legend>
                {context.asks.birthday ? (
                  <label>Tu cumpleaños
                    <input type="date" value={birthday} max={new Date().toISOString().slice(0, 10)} onChange={(event) => { setBirthday(event.target.value); clearError(); }} />
                  </label>
                ) : null}
                {context.asks.email ? (
                  <label>Tu correo
                    <input type="email" inputMode="email" autoComplete="email" value={email} placeholder="nombre@correo.com" onChange={(event) => { setEmail(event.target.value); clearError(); }} />
                  </label>
                ) : null}
                {context.asks.source ? (
                  <label>¿Cómo nos conociste?
                    <select value={source} onChange={(event) => setSource(event.target.value)}>
                      <option value="">Elige una opción</option>
                      {context.sourceOptions.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}
                    </select>
                  </label>
                ) : null}
              </fieldset>
            ) : null}
            <label className="feedbackConsent">
              <input type="checkbox" checked={whatsappOptIn} onChange={(event) => setWhatsappOptIn(event.target.checked)} />
              <span>
                Acepto recibir promociones y novedades de SSENSUUM por WhatsApp. Puedes darte de baja cuando quieras.{' '}
                <a href="/aviso-de-privacidad" target="_blank" rel="noreferrer">Aviso de privacidad</a>
              </span>
            </label>
            {error ? <p className="feedbackError" role="alert">{error}</p> : null}
            <button type="submit" className="btn btnBlock" disabled={sending}>{sending ? 'Enviando…' : 'Enviar calificación'}</button>
          </form>
        ) : null}

        {step === 'thanks' ? (
          <div className="feedbackDone">
            <span className="kicker">Gracias</span>
            <h2 id="feedback-title">{happy ? '¡Qué gusto que lo disfrutaras!' : 'Gracias por decírnoslo'}</h2>
            <p className="feedbackLead">
              {happy
                ? 'Tu próxima hora te espera. Aparta con anticipo y cancela sin costo hasta 3 horas antes.'
                : 'Lo revisamos con el equipo para que tu próxima visita sea mejor. Si quieres contarnos más, escríbenos.'}
            </p>
            <a className="btn btnBlock" href={rebookHref(context)} onClick={() => track('reserve_click', 'calificacion')}>
              {context.therapistIds.length === 1 && therapist ? `Reservar de nuevo con ${therapist}` : 'Reservar mi próxima visita'}
            </a>
            {happy ? null : (
              <a className="btn btnOutline btnBlock" href={whatsappUrl('Hola SSENSUUM, quiero contarles cómo me fue en mi visita.')} target="_blank" rel="noreferrer" onClick={() => track('whatsapp_click', 'calificacion')}>
                Escribir por WhatsApp
              </a>
            )}
          </div>
        ) : null}

        {step === 'answered' ? (
          <div className="feedbackDone">
            <span className="kicker">Gracias</span>
            <h2 id="feedback-title">Ya calificaste esta visita</h2>
            <p className="feedbackLead">Gracias por ayudarnos a mejorar. ¿Agendamos la siguiente?</p>
            <a className="btn btnBlock" href={rebookHref(context)} onClick={() => track('reserve_click', 'calificacion')}>Reservar mi próxima visita</a>
          </div>
        ) : null}

      </div>
    </div>
  );
}
