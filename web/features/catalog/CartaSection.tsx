'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ChevronIcon } from '../../components/icons';
import { track } from '../../lib/api';
import { money } from '../../lib/format';
import type { Service } from '../../lib/types';
import { whatsappUrl, WHATSAPP_MESSAGES } from '../../lib/whatsapp';
import { CARTA_GROUPS, cartaGroupFor } from './content';

function hours(minutes: number) {
  return minutes % 60 === 0 ? `${minutes / 60} h` : `${minutes} min`;
}

// Precio común de los masajes individuales; si no coincide entre todos, se muestra "desde".
function commonPrice(services: Service[]) {
  const singles = services.filter((service) => service.therapistsRequired === 1);
  if (!singles.length) return null;
  const minPublic = Math.min(...singles.map((service) => service.publicPrice));
  const minMember = Math.min(...singles.map((service) => service.memberPrice));
  const uniform = singles.every((service) => service.publicPrice === minPublic && service.memberPrice === minMember);
  return { duration: hours(singles[0].durationMinutes), publicPrice: minPublic, memberPrice: minMember, uniform };
}

export function CartaSection({ services }: { services: Service[] }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const common = commonPrice(services);

  return (
    <section className="section" id="masajes" data-testid="catalog" aria-labelledby="carta-title">
      <div className="wrap">
        <p className="label">Carta completa</p>
        <h2 id="carta-title">Todas las técnicas</h2>
        {common ? (
          <p className="cartaSummary">
            <span>Todas: {common.duration}</span>
            <span className="price">{common.uniform ? '' : 'desde '}{money(common.publicPrice)}</span>
            <a className="memberPrice" href="#membresia">{money(common.memberPrice)} miembros</a>
          </p>
        ) : null}
        <div className="cartaActions">
          <button type="button" className="btn btnOutline" aria-expanded={open} aria-controls="carta-list" onClick={() => setOpen(!open)}>
            {open ? 'Ocultar técnicas' : 'Ver todas las técnicas'}
          </button>
          <a
            className="btn btnOutline"
            href={whatsappUrl(WHATSAPP_MESSAGES.help)}
            target="_blank"
            rel="noreferrer"
            onClick={() => track('whatsapp_click', 'no-se-cual-elegir')}
          >
            No sé cuál elegir
          </a>
        </div>

        <div id="carta-list" hidden={!open}>
          {CARTA_GROUPS.map((group) => {
            const rows = services.filter((service) => cartaGroupFor(service) === group.key);
            if (!rows.length) return null;
            return (
              <div className="cartaGroup" key={group.key}>
                <h3>{group.title}</h3>
                <ul className="services">
                  {rows.map((service) => (
                    <li className="service" key={service.id} data-testid="service-card">
                      <h4>{service.name}</h4>
                      <p>{service.description}</p>
                      {group.key === 'dos' ? (
                        <p className="priceLine">
                          <span className="price">{money(service.publicPrice)}</span>
                          <a className="memberPrice" href="#membresia">{money(service.memberPrice)} miembros</a>
                        </p>
                      ) : null}
                      {service.details ? (
                        <details className="howTo">
                          <summary>Cómo se realiza <ChevronIcon /></summary>
                          <p>{service.details}</p>
                        </details>
                      ) : null}
                      {/* Botón (no enlace): el contrato de QA busca role=button "Reservar" dentro de service-card. */}
                      <button
                        type="button"
                        className="btn"
                        onClick={() => { track('reserve_click', service.id); router.push(`/reservar?service=${service.id}`); }}
                      >
                        Reservar
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
