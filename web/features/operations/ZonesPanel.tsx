'use client';

import { ChangeEvent, useEffect, useState } from 'react';
import { addOpsPoint, deleteOpsPoint, getOpsZones, uploadOpsZonePhoto } from '../../lib/api';
import type { OpsMeta, OpsZone } from '../../lib/types';
import { ZonePhoto } from './ZonePhoto';

// Configuración: la foto de cada zona y sus puntos. Se elige el tipo, se escribe qué hacer y se toca la foto.
export function ZonesPanel({ meta }: { meta: OpsMeta }) {
  const [zones, setZones] = useState<OpsZone[] | null>(null);
  const [zoneId, setZoneId] = useState('');
  const [kind, setKind] = useState(meta.pointKinds[0]?.id ?? 'limpiar');
  const [label, setLabel] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    getOpsZones()
      .then((rows) => { setZones(rows); setZoneId((current) => current || rows[0]?.id || ''); })
      .catch((e: Error) => setError(e.message));
  }, []);

  function run(action: Promise<OpsZone[]>) {
    setBusy(true);
    setError('');
    action.then(setZones).catch((e: Error) => setError(e.message)).finally(() => setBusy(false));
  }

  function upload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (file) run(uploadOpsZonePhoto(zoneId, file));
  }

  function place(x: number, y: number) {
    if (busy) return;
    if (!label.trim()) {
      setError('Escribe qué hay que hacer en el punto antes de tocar la foto.');
      return;
    }
    run(addOpsPoint(zoneId, { x, y, kind, label }));
  }

  const zone = zones?.find((row) => row.id === zoneId);

  return (
    <section className="adminCard" data-testid="ops-zones">
      <h2>Zonas y puntos</h2>
      <p className="muted">Sube una foto por zona. Después elige el tipo de punto, escribe qué hay que hacer y toca la foto donde va.</p>
      {error ? <div className="errorBox" role="alert">{error}</div> : null}
      {zones === null && !error ? <p className="muted">Cargando…</p> : null}
      {zones ? (
        <div className="recordForm">
          <div className="recordGrid">
            <label>Zona
              <select value={zoneId} onChange={(event) => setZoneId(event.target.value)} data-testid="ops-zone-select">
                {zones.map((row) => <option key={row.id} value={row.id}>{row.name} ({row.points.length} puntos{row.photoUrl ? '' : ', sin foto'})</option>)}
              </select>
            </label>
            <label>{zone?.photoUrl ? 'Cambiar foto' : 'Subir foto'}
              <input type="file" accept="image/jpeg,image/png,image/webp" onChange={upload} disabled={busy || !zoneId} />
            </label>
            <label>Tipo de punto
              <select value={kind} onChange={(event) => setKind(event.target.value)}>
                {meta.pointKinds.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}
              </select>
            </label>
            <label>Qué hay que hacer
              <input value={label} onChange={(event) => setLabel(event.target.value)} maxLength={120} placeholder="Espejo, jabón, maceta…" data-testid="ops-point-label" />
            </label>
          </div>
        </div>
      ) : null}
      {zone ? (
        <>
          <ZonePhoto zone={zone} onPlace={zone.photoUrl ? place : undefined} />
          {zone.points.length ? (
            <ol className="opsPointList">
              {zone.points.map((point) => (
                <li key={point.id}>
                  <span className={`opsKind kind-${point.kind}`} aria-hidden="true" />
                  <span>{point.kindLabel}: {point.label}</span>
                  <button type="button" className="linkButton" disabled={busy} onClick={() => run(deleteOpsPoint(point.id))}>Borrar</button>
                </li>
              ))}
            </ol>
          ) : null}
        </>
      ) : null}
    </section>
  );
}
