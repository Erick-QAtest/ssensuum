'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import Link from 'next/link';
import { getAvailability, getServices, getTherapists, track } from '../../lib/api';
import { money } from '../../lib/format';
import type { Service, Therapist } from '../../lib/types';
import { whatsappUrl, WHATSAPP_MESSAGES } from '../../lib/whatsapp';
import { localIsoDate, timeLabel } from '../booking/dates';
import {
  inWindow,
  lowerFirst,
  pickMassage,
  pickTherapist,
  QUESTIONS,
  quizMessage,
  saveQuizAnswers,
  reserveHref,
  resolveService,
  therapistChoices,
  TIME_WINDOWS,
  type Answers,
  type TimeWindow,
} from './quiz';

const DAYS_TO_SEARCH = 3;
const MAX_SLOTS = 4;

type Slot = { date: string; time: string; dayLabel: string };
type SlotState = { status: 'loading' | 'ready'; items: Slot[] };

function dayLabel(date: Date, offset: number) {
  if (offset === 0) return 'Hoy';
  if (offset === 1) return 'Mañana';
  const label = date.toLocaleDateString('es-MX', { weekday: 'short', day: 'numeric' });
  return label.charAt(0).toUpperCase() + label.slice(1);
}

// Hasta dos horarios por día, separados al menos 2 h, para dar opciones distintas.
function spread(times: string[]) {
  if (!times.length) return [];
  const minutes = (time: string) => Number(time.slice(0, 2)) * 60 + Number(time.slice(3, 5));
  const first = times[0];
  const later = times.find((time) => minutes(time) - minutes(first) >= 120) ?? times[times.length - 1];
  return later !== first ? [first, later] : [first];
}

function Face({ therapist, className }: { therapist: Therapist; className: string }) {
  if (therapist.photoUrl) {
    return <img className={className} src={therapist.photoUrl} alt={`${therapist.name}, terapeuta de SSENSUUM`} />;
  }
  return <span className={`${className} quizInitial`} aria-hidden="true">{therapist.name.slice(0, 1)}</span>;
}

export function TherapistQuiz() {
  const [services, setServices] = useState<Service[]>([]);
  const [therapists, setTherapists] = useState<Therapist[]>([]);
  const [loadError, setLoadError] = useState(false);
  const [step, setStep] = useState(-1);
  const [answers, setAnswers] = useState<Answers>({});
  // undefined = la recomendación del quiz; null = sin preferencia.
  const [override, setOverride] = useState<Therapist | null | undefined>(undefined);
  const [slots, setSlots] = useState<SlotState>({ status: 'loading', items: [] });
  const headingRef = useRef<HTMLHeadingElement>(null);
  const advanceTimer = useRef<number | undefined>(undefined);
  const resultTracked = useRef(false);

  useEffect(() => {
    Promise.all([getServices(), getTherapists()])
      .then(([serviceRows, therapistRows]) => {
        setServices(serviceRows);
        setTherapists(therapistRows);
      })
      .catch(() => setLoadError(true));
    track('page_view', 'quiz');
    return () => window.clearTimeout(advanceTimer.current);
  }, []);

  useEffect(() => {
    if (step < 0) return;
    headingRef.current?.focus({ preventScroll: true });
    window.scrollTo({ top: 0 });
  }, [step]);

  const isResult = step >= QUESTIONS.length;
  const pick = useMemo(() => resolveService(pickMassage(answers), services), [answers, services]);
  const recommended = useMemo(() => pickTherapist(answers, therapists), [answers, therapists]);
  const therapist = override === undefined ? recommended : override;
  const window_ = (answers.horario ?? 'tarde') as TimeWindow;
  const faces = therapists.filter((row) => row.photoUrl);

  useEffect(() => {
    if (!isResult || resultTracked.current) return;
    resultTracked.current = true;
    track('page_view', 'quiz:resultado');
    saveQuizAnswers(answers);
  }, [isResult, answers]);

  // Próximos horarios reales en la ventana elegida (hoy y los dos días siguientes).
  useEffect(() => {
    if (!isResult || !pick) return;
    let cancelled = false;
    setSlots({ status: 'loading', items: [] });
    const days = Array.from({ length: DAYS_TO_SEARCH }, (_, offset) => {
      const date = new Date();
      date.setDate(date.getDate() + offset);
      return { date, offset };
    });
    Promise.all(
      days.map(({ date, offset }) =>
        getAvailability(pick.service.id, localIsoDate(date), therapist?.id)
          .then((rows) => spread(rows.filter((time) => inWindow(time, window_))).map((time) => ({ date: localIsoDate(date), time, dayLabel: dayLabel(date, offset) })))
          .catch(() => [] as Slot[]),
      ),
    ).then((perDay) => {
      if (!cancelled) setSlots({ status: 'ready', items: perDay.flat().slice(0, MAX_SLOTS) });
    });
    return () => {
      cancelled = true;
    };
  }, [isResult, pick, therapist, window_]);

  function answer(value: string) {
    const question = QUESTIONS[step];
    setAnswers((current) => ({ ...current, [question.id]: value }));
    if (question.id === 'trato') setOverride(undefined);
    window.clearTimeout(advanceTimer.current);
    advanceTimer.current = window.setTimeout(() => setStep((current) => current + 1), 160);
  }

  function restart() {
    setAnswers({});
    setOverride(undefined);
    resultTracked.current = false;
    setStep(-1);
    window.scrollTo({ top: 0 });
  }

  return (
    <main className="quizShell">
      <div className="quizTop">
        <Link href="/" className="backLink">← SSENSUUM</Link>
      </div>

      <div className="quizBody">
        {step < 0 ? (
          <section className="quizScreen" aria-labelledby="quiz-title">
            <p className="label">Quiz · 1 minuto</p>
            <h1 id="quiz-title" className="quizTitle">¿Qué terapeuta va <em>contigo?</em></h1>
            <p className="quizLead">
              Cinco preguntas. Al final te recomendamos terapeuta, masaje y horario, con los espacios que hay libres para apartar.
            </p>
            {faces.length ? (
              <div className="heroFaces" aria-label={`${therapists.length} terapeutas en el equipo`}>
                <span>{faces.map((row) => <img key={row.id} src={row.photoUrl} alt="" />)}</span>
              </div>
            ) : null}
            <ul className="chips" aria-label="Lo que recibes">
              <li className="chip">Tu terapeuta</li>
              <li className="chip">Tu masaje</li>
              <li className="chip">Tu horario</li>
            </ul>
            <button type="button" className="btn btnBlock" onClick={() => setStep(0)}>Empezar</button>
            <p className="quizNote">Tu visita es confidencial.</p>
          </section>
        ) : null}

        {step >= 0 && !isResult ? (
          <section className="quizScreen" aria-labelledby="quiz-question">
            <div className="quizProgress" aria-hidden="true">
              {QUESTIONS.map((question, index) => <span key={question.id} className={index <= step ? 'on' : ''} />)}
            </div>
            <p className="label">Pregunta {step + 1} de {QUESTIONS.length}</p>
            <h1 id="quiz-question" className="quizQuestion" tabIndex={-1} ref={headingRef}>{QUESTIONS[step].title}</h1>
            <div className="quizOptions" role="group" aria-labelledby="quiz-question">
              {QUESTIONS[step].options.map((option) => (
                <button
                  type="button"
                  key={option.value}
                  className="quizOption"
                  aria-pressed={answers[QUESTIONS[step].id] === option.value}
                  onClick={() => answer(option.value)}
                >
                  {option.label}
                  {option.hint ? <small>{option.hint}</small> : null}
                </button>
              ))}
            </div>
            <button type="button" className="quizLink" onClick={() => setStep(step - 1)}>Atrás</button>
          </section>
        ) : null}

        {isResult ? (
          <section className="quizScreen" aria-labelledby="quiz-result">
            <p className="label">Tu recomendación</p>
            {!pick ? (
              <>
                <h1 id="quiz-result" className="quizQuestion" tabIndex={-1} ref={headingRef}>Te ayudamos por WhatsApp.</h1>
                <div className="errorBox" role="alert">
                  {loadError ? 'No pudimos cargar la carta y el equipo en este momento.' : 'Estamos cargando la carta…'}
                </div>
                <a
                  className="btn btnBlock"
                  href={whatsappUrl(WHATSAPP_MESSAGES.help)}
                  target="_blank"
                  rel="noreferrer"
                  onClick={() => track('whatsapp_click', 'quiz')}
                >
                  Escribir por WhatsApp
                </a>
              </>
            ) : (
              <>
                <h1 id="quiz-result" className="quizQuestion" tabIndex={-1} ref={headingRef}>
                  {therapist ? (
                    <>{therapist.name}, con <em>{lowerFirst(pick.service.name)}.</em></>
                  ) : (
                    <><em>{pick.service.name},</em> con quien tenga espacio.</>
                  )}
                </h1>

                <div className="quizPanel">
                  <div className="quizRow quizRowTherapist">
                    {therapist ? <Face therapist={therapist} className="quizFace" /> : <span className="quizFace quizInitial" aria-hidden="true">?</span>}
                    <div>
                      <p className="label">Tu terapeuta</p>
                      <h2 className="quizName">
                        {therapist ? therapist.name : 'El que tenga espacio'}
                        {therapist?.isNew ? <span className="tag">Nuevo</span> : null}
                      </h2>
                      {therapist?.strengths ? (
                        <ul className="chips" aria-label="Fortalezas">
                          {therapist.strengths.split('·').map((item) => item.trim()).filter(Boolean).map((item) => <li className="chip" key={item}>{item}</li>)}
                        </ul>
                      ) : null}
                    </div>
                    {therapist?.bio ? <p className="quizText quizBio">{therapist.bio}</p> : null}
                    {!therapist ? <p className="quizText quizBio">Te asignamos al terapeuta libre en tu horario.</p> : null}
                  </div>

                  <div className="quizRow">
                    <div>
                      <p className="label">Tu masaje</p>
                      <h2 className="quizName">{pick.service.name}</h2>
                      <p className="quizText">{pick.why}</p>
                      <p className="priceLine">
                        <span className="price">{money(pick.service.publicPrice)}</span>
                        <Link className="memberPrice" href="/#membresia">{money(pick.service.memberPrice)} miembros</Link>
                        <span>{pick.service.durationMinutes % 60 === 0 ? `${pick.service.durationMinutes / 60} h` : `${pick.service.durationMinutes} min`}</span>
                      </p>
                    </div>
                  </div>

                  <div className="quizRow">
                    <div>
                      <p className="label">Tu horario · {lowerFirst(TIME_WINDOWS[window_].label)}</p>
                      {slots.status === 'loading' ? <p className="quizText">Buscando espacios libres…</p> : null}
                      {slots.status === 'ready' && slots.items.length ? (
                        <ul className="quizSlots" aria-label="Próximos espacios libres">
                          {slots.items.map((slot) => (
                            <li key={`${slot.date}-${slot.time}`}>
                              <Link
                                className="quizSlot"
                                href={reserveHref(pick.service, therapist, slot)}
                                onClick={() => track('reserve_click', `quiz:${therapist?.id ?? 'sin-preferencia'}`)}
                              >
                                <span>{slot.dayLabel}</span>
                                <strong>{timeLabel(slot.time)}</strong>
                              </Link>
                            </li>
                          ))}
                        </ul>
                      ) : null}
                      {slots.status === 'ready' && !slots.items.length ? (
                        <p className="quizText">No hay espacios {lowerFirst(TIME_WINDOWS[window_].label)} en los próximos {DAYS_TO_SEARCH} días. Elige otro día al reservar o escríbenos.</p>
                      ) : null}
                    </div>
                  </div>
                </div>

                <div className="quizActions">
                  <Link
                    className="btn btnBlock"
                    href={reserveHref(pick.service, therapist)}
                    onClick={() => track('reserve_click', `quiz:${therapist?.id ?? 'sin-preferencia'}`)}
                  >
                    {therapist ? `Reservar con ${therapist.name}` : 'Reservar'}
                  </Link>
                  <a
                    className="btn btnOutline btnBlock"
                    href={whatsappUrl(quizMessage(therapist, pick.service, window_))}
                    target="_blank"
                    rel="noreferrer"
                    onClick={() => track('whatsapp_click', 'quiz')}
                  >
                    Prefiero escribir por WhatsApp
                  </a>
                </div>

                <fieldset className="quizSwitch">
                  <legend className="label">¿Prefieres a otro terapeuta?</legend>
                  <div className="quizPicks">
                    {therapistChoices(answers, therapists).map((row) => (
                      <button
                        type="button"
                        key={row.id}
                        className="quizPick"
                        aria-pressed={therapist?.id === row.id}
                        onClick={() => setOverride(row)}
                      >
                        <Face therapist={row} className="quizPickFace" />
                        {row.name}
                      </button>
                    ))}
                    <button type="button" className="quizPick" aria-pressed={!therapist} onClick={() => setOverride(null)}>
                      Sin preferencia
                    </button>
                  </div>
                </fieldset>

                <p className="quizNote">
                  Apartas con {money(pick.service.deposit)}, que se descuentan de tu total. Si la presión o el ambiente no son lo que esperabas, lo ajustamos en los primeros 10 minutos.
                </p>
                <button type="button" className="quizLink" onClick={restart}>Volver a empezar</button>
              </>
            )}
          </section>
        ) : null}
      </div>
    </main>
  );
}
