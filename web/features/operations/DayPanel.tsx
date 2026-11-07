'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { checkOpsItem, closeOpsDay, getOpsDay, reopenOpsDay, uncheckOpsItem, uploadOpsEvidence } from '../../lib/api';
import { compressPhoto } from './compress';
import type { OpsDay, OpsPoint, OpsTask } from '../../lib/types';
import { ZonePhoto } from './ZonePhoto';

const SHIFTS = ['apertura', 'cierre'];

function hours(minutes: number) {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return h ? `${h} h${m ? ` ${m} min` : ''}` : `${m} min`;
}

// El día de recepción: cada tarea se marca como hecha o "no se pudo" con su motivo; el día se cierra con todo marcado.
export function DayPanel({ day, today }: { day: string; today: string }) {
  const [data, setData] = useState<OpsDay | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    setData(null);
    setError('');
    getOpsDay(day).then(setData).catch((e: Error) => setError(e.message));
  }, [day]);

  const run = useCallback((action: Promise<OpsDay>) => {
    setBusy(true);
    setError('');
    action.then(setData).catch((e: Error) => setError(e.message)).finally(() => setBusy(false));
  }, []);

  function mark(key: string) {
    run(checkOpsItem(day, key, 'hecho'));
  }

  function fail(key: string, label: string) {
    const reason = window.prompt(`¿Por qué no se pudo "${label}"?`);
    if (reason === null) return;
    if (!reason.trim()) {
      setError('Escribe el motivo para marcarlo como "no se pudo".');
      return;
    }
    run(checkOpsItem(day, key, 'no_se_pudo', reason));
  }

  function undo(key: string) {
    run(uncheckOpsItem(day, key));
  }

  function uploadEvidence(task: OpsTask, zoneId: string, pointId: string | null, file: File | undefined) {
    if (!file) return;
    setBusy(true);
    setError('');
    compressPhoto(file)
      .then((photo) => uploadOpsEvidence(day, task.key, zoneId, pointId, photo))
      .then(setData)
      .catch((e: Error) => setError(e.message))
      .finally(() => setBusy(false));
  }

  function togglePoint(task: OpsTask, point: OpsPoint) {
    if (data?.closed || busy || day > today) return;
    const key = `${task.key}@${point.id}`;
    if (point.status === 'pendiente') mark(key);
    else undo(key);
  }

  if (error && !data) return <div className="errorBox" role="alert">{error}</div>;
  if (!data) return <p className="muted">Cargando el día…</p>;

  const locked = data.closed || busy;
  const future = data.day > today;

  return (
    <>
      <section className="adminCard" data-testid="ops-day">
        <div className="adminRow adminRowSpread">
          <div>
            <h2>{data.weekday} · semana {data.cycleWeek}</h2>
            <p className="muted">{data.tasks.length} tareas · {hours(data.minutes)} sin contar servicios</p>
          </div>
          <span className={`statusBadge ${data.closed ? 'ok' : data.pending ? 'wait' : 'ok'}`} data-testid="ops-status">
            {data.closed ? 'Día cerrado' : data.pending ? `Faltan ${data.pending}` : 'Listo para cerrar'}
          </span>
        </div>
        {future ? <p className="muted">Es un día futuro: puedes ver qué toca, pero se marca hasta ese día.</p> : null}
        {error ? <div className="errorBox" role="alert">{error}</div> : null}
      </section>

      {SHIFTS.map((shift) => {
        const tasks = data.tasks.filter((task) => task.shift === shift);
        if (!tasks.length) return null;
        return (
          <section key={shift} className="adminCard">
            <h2>{tasks[0].shiftLabel}</h2>
            <ul className="opsTasks">
              {tasks.map((task) => (
                <li key={task.key} className={`opsTask status-${task.status}`} data-testid="ops-task">
                  <div className="adminRow adminRowSpread opsTaskHead">
                    <div>
                      <h3>{task.label}</h3>
                      <span className="adminSub">{task.minutes} min{task.detail ? ` · ${task.detail}` : ''}</span>
                    </div>
                    <span className={`statusBadge ${task.status === 'hecho' ? 'ok' : 'wait'}`}>
                      {task.status === 'hecho' ? 'Hecho' : task.status === 'no_se_pudo' ? 'No se pudo' : 'Pendiente'}
                    </span>
                  </div>
                  {task.reason ? <p className="opsReason">Motivo: {task.reason}</p> : null}

                  {task.posts.length ? (
                    <ul className="opsPosts">
                      {task.posts.map((post) => (
                        <li key={post.id}>{post.status === 'publicado' ? '✓' : '○'} {post.channel} · {post.title}</li>
                      ))}
                      <li><Link href="/admin/marketing">Marcar como publicadas en Marketing →</Link></li>
                    </ul>
                  ) : null}

                  {task.supplies.length ? (
                    <ul className="opsPosts" data-testid="ops-supplies">
                      {task.supplies.map((row) => (
                        <li key={row.name}>{row.status === 'urgente' ? '⚠ ' : ''}{row.name}: {row.quantity} {row.unit}</li>
                      ))}
                    </ul>
                  ) : task.key === 'pedido' ? <p className="muted">Nada que pedir esta semana según el inventario.</p> : null}

                  {task.zones.map((zone) => (
                    <div key={zone.id} className="opsZone">
                      <p className="planLabel">{zone.name} · toca cada punto al terminarlo</p>
                      <ZonePhoto zone={zone} onPoint={(point) => togglePoint(task, point)} />
                      <ol className="opsPointList">
                        {zone.points.map((point) => (
                          <li key={point.id} className={`status-${point.status}`}>
                            <span className={`opsKind kind-${point.kind}`} aria-hidden="true" />
                            <span>{point.kindLabel}: {point.label}{point.reason ? ` · No se pudo: ${point.reason}` : ''}</span>
                            {!data.closed && point.status === 'pendiente' ? (
                              <button type="button" className="linkButton" disabled={locked} onClick={() => fail(`${task.key}@${point.id}`, point.label)}>No se pudo</button>
                            ) : null}
                          </li>
                        ))}
                      </ol>
                    </div>
                  ))}
                  {task.evidence.length ? (
                    <div className="opsEvidence">
                      {task.evidence.map((row) => (
                        <div key={`${row.zoneId}-${row.pointId ?? 'zona'}`} className="opsEvidenceItem" data-testid="ops-evidence">
                          <p className="planLabel">
                            {row.pointLabel ? `Foto al azar de hoy: ${row.zoneName} · ${row.pointLabel}` : `Foto del después: ${row.zoneName}, desde el mismo ángulo que la referencia`}
                          </p>
                          {row.photo?.url ? (
                            // eslint-disable-next-line @next/next/no-img-element
                            <img className="opsEvidenceThumb" src={row.photo.url} alt={`Evidencia de ${row.zoneName}`} />
                          ) : null}
                          {row.photo?.review === 'repetir' ? <p className="opsReason">Repetir: {row.photo.reviewNote}</p> : null}
                          {!data.closed && !future ? (
                            <label className={`secondaryButton opsCamera ${locked ? 'disabled' : ''}`}>
                              {row.photo ? 'Tomar otra foto' : 'Tomar foto'}
                              <input
                                type="file"
                                accept="image/*"
                                capture="environment"
                                disabled={locked}
                                onChange={(event) => { uploadEvidence(task, row.zoneId, row.pointId, event.target.files?.[0]); event.target.value = ''; }}
                                data-testid="ops-evidence-input"
                              />
                            </label>
                          ) : null}
                        </div>
                      ))}
                    </div>
                  ) : null}
                  {task.zonesWithoutPoints?.length && task.zones.length ? (
                    <p className="muted">Sin foto todavía: {task.zonesWithoutPoints.join(', ')}. Al terminarlas, marca la tarea como hecha.</p>
                  ) : null}

                  {!data.closed ? (
                    <div className="adminRow">
                      {task.status === 'pendiente' && !task.posts.length && (!task.zones.length || task.zonesWithoutPoints?.length) ? (
                        <button type="button" className="primaryButton" disabled={locked || future} onClick={() => mark(task.key)} data-testid="ops-done">
                          {task.zones.length ? 'Zonas sin foto: hechas' : 'Hecho'}
                        </button>
                      ) : null}
                      {task.status === 'pendiente' ? (
                        <button type="button" className="secondaryButton" disabled={locked || future} onClick={() => fail(task.key, task.label)}>No se pudo</button>
                      ) : (
                        <button type="button" className="linkButton" disabled={locked} onClick={() => undo(task.key)}>Deshacer</button>
                      )}
                    </div>
                  ) : null}
                </li>
              ))}
            </ul>
          </section>
        );
      })}

      <section className="adminCard">
        {data.closed ? (
          <div className="adminRow adminRowSpread">
            <p>Día cerrado. Si hay que corregir algo, reábrelo.</p>
            <button type="button" className="secondaryButton" disabled={busy} onClick={() => run(reopenOpsDay(day))}>Reabrir día</button>
          </div>
        ) : (
          <div className="adminRow adminRowSpread">
            <p className="muted">{data.pending ? `Para cerrar el día faltan ${data.pending} tareas.` : 'Todo está marcado.'}</p>
            <button type="button" className="primaryButton" disabled={!data.canClose || busy} onClick={() => run(closeOpsDay(day))} data-testid="ops-close">Cerrar día</button>
          </div>
        )}
      </section>
    </>
  );
}
