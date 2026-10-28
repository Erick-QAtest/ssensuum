import { money } from '../../lib/format';
import type { Service } from '../../lib/types';

function duration(minutes: number) {
  return minutes % 60 === 0 ? `${minutes / 60} h` : `${minutes} min`;
}

// Renglón de la lista de precios de barbería y medicina estética; se reservan por WhatsApp, un botón por grupo.
export function ServiceRow({ service }: { service: Service }) {
  return (
    <li className="priceItem">
      <span className="priceName">{service.name} <span className="priceMeta">{duration(service.durationMinutes)}</span></span>
      <span className="priceAmount">
        {money(service.publicPrice)}
        <a className="priceMeta" href="#membresia">{money(service.memberPrice)} miembros</a>
      </span>
    </li>
  );
}
