'use client';

import { FormEvent, useEffect, useState } from 'react';
import { deleteChannelSnapshot, getChannelMetrics, saveChannelSnapshot } from '../../lib/api';
import type { ChannelMetrics, MarketingMeta, MetricKey } from '../../lib/types';
import { localIsoDate } from '../booking/dates';
import { count, shortDay, signed } from './marketing';

const FIELDS: { key: MetricKey; input: 'followers' | 'reach' | 'interactions' | 'linkClicks' }[] = [
  { key: 'followers', input: 'followers' },
  { key: 'reach', input: 'reach' },
  { key: 'interactions', input: 'interactions' },
  { key: 'link_clicks', input: 'linkClicks' },
];

function Change({ value }: { value: number | null }) {
  const text = signed(value);
  if (!text) return null;
  return <span className={`financeDelta ${value! > 0 ? 'good' : 'bad'}`}>{text}</span>;
}

export function MetricsPanel({ meta }: { meta: MarketingMeta }) {
  const [rows, setRows] = useState<ChannelMetrics[] | null>(null);
  const [channel, setChannel] = useState(meta.channels[0]?.id ?? 'instagram');
  const [day, setDay] = useState(() => localIsoDate(new Date()));
  const [values, setValues] = useState<Record<MetricKey, string>>({ followers: '', reach: '', interactions: '', link_clicks: '' });
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const labels = Object.fromEntries(meta.metrics.map((option) => [option.id, option.label])) as Record<MetricKey, string>;

  useEffect(() => {
    getChannelMetrics().then(setRows).catch((e: Error) => setError(e.message));
  }, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError('');
    const number = (key: MetricKey) => (values[key].trim() === '' ? null : Math.max(0, Math.round(Number(values[key]))));
    try {
      setRows(await saveChannelSnapshot({
        channel,
        day,
        followers: number('followers'),
        reach: number('reach'),
        interactions: number('interactions'),
        linkClicks: number('link_clicks'),
      }));
      setValues({ followers: '', reach: '', interactions: '', link_clicks: '' });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  }

  async function remove(id: string) {
    if (!window.confirm('¿Borrar esta captura?')) return;
    try {
      await deleteChannelSnapshot(id);
      setRows(await getChannelMetrics());
    } catch (e) {
      setError((e as Error).message);
    }
  }

  const filled = Object.values(values).some((value) => value.trim() !== '');

  return (
    <>
      <form className="adminCard recordForm" onSubmit={submit} data-testid="metrics-form">
        <h2>Capturar métricas</h2>
        <p className="muted">
          Una vez por semana, copia los números de las estadísticas de cada red (Instagram: Panel profesional; TikTok: Estadísticas; X: Analytics;
          Facebook: Meta Business Suite). Capturar dos veces el mismo día corrige la captura.
        </p>
        <div className="recordGrid">
          <label>Red
            <select value={channel} onChange={(event) => setChannel(event.target.value)}>
              {meta.channels.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}
            </select>
          </label>
          <label>Fecha
            <input type="date" value={day} max={localIsoDate(new Date())} onChange={(event) => setDay(event.target.value)} required />
          </label>
          {FIELDS.map((field) => (
            <label key={field.key}>{labels[field.key]}
              <input
                type="number"
                min={0}
                inputMode="numeric"
                value={values[field.key]}
                onChange={(event) => setValues((current) => ({ ...current, [field.key]: event.target.value }))}
                placeholder="Opcional"
              />
            </label>
          ))}
        </div>
        {error ? <div className="errorBox" role="alert">{error}</div> : null}
        <div className="adminRow">
          <button type="submit" className="primaryButton" disabled={saving || !filled} data-testid="metrics-save">Guardar captura</button>
        </div>
      </form>

      {rows === null && !error ? <p className="muted">Cargando…</p> : null}
      <div className="marketingChannels">
        {rows?.map((row) => {
          const latest = row.snapshots[0];
          return (
            <section key={row.channel} className="adminCard" data-testid="channel-metrics">
              <div className="adminRow adminRowSpread">
                <h2>{row.label}</h2>
                {latest?.followers !== null && latest?.followers !== undefined ? (
                  <div className="marketingFollowers">
                    <strong>{count(latest.followers)}</strong> seguidores <Change value={latest.changes.followers} />
                  </div>
                ) : null}
              </div>
              {row.snapshots.length === 0 ? <p className="muted">Aún no hay capturas.</p> : (
                <div className="adminTableWrap">
                  <table className="adminTable">
                    <thead><tr><th>Fecha</th>{FIELDS.map((field) => <th key={field.key}>{labels[field.key]}</th>)}<th></th></tr></thead>
                    <tbody>
                      {row.snapshots.slice(0, 8).map((snapshot) => (
                        <tr key={snapshot.id}>
                          <td className="customerVisits">{shortDay(snapshot.day)}</td>
                          {FIELDS.map((field) => (
                            <td key={field.key}>{count(snapshot[field.key])} <Change value={snapshot.changes[field.key]} /></td>
                          ))}
                          <td><button type="button" className="linkButton" onClick={() => remove(snapshot.id)}>Borrar</button></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          );
        })}
      </div>
    </>
  );
}
