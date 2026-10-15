import { money } from '../../lib/format';
import type { Service } from '../../lib/types';
import { AESTHETICS } from './categories';

function duration(minutes: number) {
  return minutes % 60 === 0 ? `${minutes / 60} h` : `${minutes} min`;
}

// Fila compacta para barbería y medicina estética.
export function ServiceRow({ service, onReserve }: { service: Service; onReserve: () => void }) {
  const saving = service.publicPrice - service.memberPrice;
  return (
    <li className="compactItem" data-testid="service-card">
      <h4>{service.name} <span className="memberPrice">· {duration(service.durationMinutes)}</span></h4>
      <p>
        {money(service.publicPrice)} · <a className="memberPrice" href="#membresia">{money(service.memberPrice)} miembros</a>
        {saving > 0 ? ` · ahorras ${money(saving)}` : ''}
      </p>
      <button type="button" className="btn" onClick={onReserve}>
        {service.category === AESTHETICS ? 'Agendar valoración' : 'Reservar'}
      </button>
    </li>
  );
}
