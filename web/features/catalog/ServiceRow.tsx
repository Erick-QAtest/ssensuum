import { money } from '../../lib/format';
import type { Service } from '../../lib/types';
import { AESTHETICS } from './categories';

function serviceButtonLabel(category: string) {
  return category === AESTHETICS ? 'Agendar valoración' : 'Reservar';
}

export function ServiceRow({ service, onReserve, compact = false }: { service: Service; onReserve: () => void; compact?: boolean }) {
  return (
    <article className={`fusionServiceRow ${compact ? 'fusionServiceRowCompact' : ''}`} data-testid="service-card">
      <div className="fusionServiceText">
        <div className="fusionServiceTitleLine">
          <h3>{service.name}</h3>
          {service.id === 'massage-special' ? <span className="fusionTag">El más elegido</span> : null}
          {service.therapistsRequired === 2 ? <span className="fusionTag fusionTagSoft">{service.name.toLowerCase().includes('pareja') ? 'Para dos personas' : 'Dos terapeutas'}</span> : null}
        </div>
        {!compact ? <p>{service.description}</p> : null}
        <small>{service.durationMinutes >= 60 ? `${Math.round(service.durationMinutes / 60 * 10) / 10} h` : `${service.durationMinutes} min`}</small>
      </div>
      <div className="fusionServicePurchase">
        <strong>{money(service.publicPrice)}</strong>
        <span>público general</span>
        <small>{money(service.memberPrice)} miembros</small>
        <button type="button" className="fusionButton fusionButtonSmall" onClick={onReserve}>{serviceButtonLabel(service.category)}</button>
      </div>
    </article>
  );
}
