'use client';

import type { MouseEvent } from 'react';
import type { OpsPoint, OpsZone } from '../../lib/types';

type Props = {
  zone: OpsZone;
  onPoint?: (point: OpsPoint) => void;
  // Para colocar puntos nuevos: devuelve la posición del clic en fracciones de la foto (0 a 1).
  onPlace?: (x: number, y: number) => void;
};

// Foto de la zona con sus puntos encima. Colores: azul limpiar, rojo rellenar, verde regar, morado revisar bolsa.
export function ZonePhoto({ zone, onPoint, onPlace }: Props) {
  function place(event: MouseEvent<HTMLDivElement>) {
    if (!onPlace) return;
    const box = event.currentTarget.getBoundingClientRect();
    onPlace((event.clientX - box.left) / box.width, (event.clientY - box.top) / box.height);
  }

  if (!zone.photoUrl) return <p className="muted">Esta zona aún no tiene foto.</p>;

  return (
    <div className={`opsPhoto ${onPlace ? 'opsPhotoPlacing' : ''}`} onClick={place} data-testid="ops-photo">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={zone.photoUrl} alt={`Foto de ${zone.name}`} draggable={false} />
      {zone.points.map((point, index) => (
        <button
          key={point.id}
          type="button"
          className={`opsDot kind-${point.kind} status-${point.status ?? 'pendiente'}`}
          style={{ left: `${point.x * 100}%`, top: `${point.y * 100}%` }}
          title={`${index + 1}. ${point.kindLabel}: ${point.label}`}
          aria-label={`${index + 1}. ${point.kindLabel}: ${point.label}${point.status === 'hecho' ? ', hecho' : ''}`}
          onClick={(event) => {
            event.stopPropagation();
            onPoint?.(point);
          }}
          data-testid="ops-dot"
        >
          {point.status === 'hecho' ? '✓' : index + 1}
        </button>
      ))}
    </div>
  );
}
