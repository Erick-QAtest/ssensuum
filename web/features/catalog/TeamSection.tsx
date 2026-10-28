'use client';

import { useEffect, useRef, useState } from 'react';
import { ChevronIcon } from '../../components/icons';
import { getAvailability, track } from '../../lib/api';
import type { Therapist } from '../../lib/types';
import { localIsoDate } from '../booking/dates';
import { SPECIAL_ID } from './content';

function strengthsOf(therapist: Therapist) {
  return therapist.strengths.split('·').map((item) => item.trim()).filter(Boolean);
}

export function TeamSection({ therapists }: { therapists: Therapist[] }) {
  const [availableToday, setAvailableToday] = useState<Set<string>>(new Set());
  // En celular el equipo es un carrusel: el contador avisa que hay más tarjetas y cuántas.
  const listRef = useRef<HTMLUListElement>(null);
  const [current, setCurrent] = useState(0);
  const onScroll = () => {
    const list = listRef.current;
    const card = list?.firstElementChild as HTMLElement | null;
    if (!list || !card) return;
    setCurrent(Math.round(list.scrollLeft / (card.offsetWidth + 16)));
  };

  // La API ya calcula horarios por terapeuta: "Disponible hoy" = le queda algún horario hoy.
  useEffect(() => {
    if (!therapists.length) return;
    const today = localIsoDate(new Date());
    Promise.all(
      therapists.map((therapist) =>
        getAvailability(SPECIAL_ID, today, therapist.id)
          .then((slots) => (slots.length ? therapist.id : null))
          .catch(() => null),
      ),
    ).then((ids) => setAvailableToday(new Set(ids.filter((id): id is string => Boolean(id)))));
  }, [therapists]);

  return (
    <section className="section" id="equipo" aria-labelledby="equipo-title">
      <div className="wrap">
        <div className="sectionHead">
          <h2 id="equipo-title">Elige quién te atiende.</h2>
          <p className="sectionLead">¿No sabes a quién elegir? <a href="/quiz">Haz el quiz de 1 minuto</a> y te recomendamos terapeuta, masaje y horario.</p>
        </div>
        {therapists.length > 1 ? (
          <p className="teamCount" aria-hidden="true">
            <span>Desliza para ver a todos</span>
            <span>{Math.min(current + 1, therapists.length)} / {therapists.length}</span>
          </p>
        ) : null}
        <ul className="team" ref={listRef} onScroll={onScroll}>
          {therapists.map((therapist) => (
            <li className="therapist" key={therapist.id}>
              <div className="therapistPhoto">
                {therapist.photoUrl ? (
                  <img src={therapist.photoUrl} alt={`${therapist.name}, terapeuta de SSENSUUM`} loading="lazy" />
                ) : (
                  <span className="therapistInitial" aria-hidden="true">{therapist.name.slice(0, 1)}</span>
                )}
              </div>
              <div className="therapistBody">
                <h3 className="therapistName">{therapist.name}</h3>
                {therapist.isNew || availableToday.has(therapist.id) ? (
                  <p className="therapistTags">
                    {therapist.isNew ? <span className="tag">Nuevo</span> : null}
                    {availableToday.has(therapist.id) ? <span className="availableToday">Disponible hoy</span> : null}
                  </p>
                ) : null}
                {strengthsOf(therapist).length ? <p className="therapistTrait">{strengthsOf(therapist).join(' · ')}</p> : null}
                {therapist.bio ? (
                  <details className="therapistMore">
                    <summary>Conoce a {therapist.name} <ChevronIcon /></summary>
                    <p>{therapist.bio}</p>
                  </details>
                ) : null}
                {therapist.isNew && !therapist.bio ? <p className="therapistTrait">Recién se integra al equipo.</p> : null}
                <a
                  className="btn"
                  href={`/reservar?service=${SPECIAL_ID}&therapist=${therapist.id}`}
                  onClick={() => track('reserve_click', `terapeuta:${therapist.id}`)}
                >
                  Reservar<span className="srOnly"> con {therapist.name}</span>
                </a>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
