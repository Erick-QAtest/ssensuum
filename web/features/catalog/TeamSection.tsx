'use client';

import { useEffect, useState } from 'react';
import { getAvailability, track } from '../../lib/api';
import type { Therapist } from '../../lib/types';
import { localIsoDate } from '../booking/dates';
import { SPECIAL_ID } from './content';

function strengthsOf(therapist: Therapist) {
  return therapist.strengths.split('·').map((item) => item.trim()).filter(Boolean);
}

export function TeamSection({ therapists }: { therapists: Therapist[] }) {
  const [availableToday, setAvailableToday] = useState<Set<string>>(new Set());

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
          <p className="label">Terapeutas</p>
          <h2 id="equipo-title">Elige quién te atiende.</h2>
        </div>
        <ul className="team">
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
                <h3 className="therapistName">
                  {therapist.name}
                  {therapist.isNew ? <span className="tag">Nuevo</span> : null}
                </h3>
                {availableToday.has(therapist.id) ? <span className="availableToday">Disponible hoy</span> : null}
                {strengthsOf(therapist).length ? (
                  <ul className="chips" aria-label="Fortalezas">
                    {strengthsOf(therapist).map((strength) => <li className="chip" key={strength}>{strength}</li>)}
                  </ul>
                ) : null}
                {therapist.bio ? <p className="therapistBio">{therapist.bio}</p> : null}
                {therapist.isNew && !therapist.bio ? <p className="therapistBio">Recién se integra al equipo SSENSUUM.</p> : null}
                <a
                  className="btn"
                  href={`/reservar?service=${SPECIAL_ID}&therapist=${therapist.id}`}
                  onClick={() => track('reserve_click', `terapeuta:${therapist.id}`)}
                >
                  Reservar con {therapist.name}
                </a>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
