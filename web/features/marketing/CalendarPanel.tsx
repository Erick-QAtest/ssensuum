'use client';

import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react';
import { deleteMarketingPost, getMarketingPosts, saveMarketingPost } from '../../lib/api';
import type { MarketingMeta, MarketingPost, MarketingPostInput } from '../../lib/types';
import { localIsoDate } from '../booking/dates';
import { monthRange, shortDay } from './marketing';

export type PostDraft = Partial<MarketingPostInput>;

function blank(meta: MarketingMeta, draft?: PostDraft): MarketingPostInput {
  return {
    channel: meta.channels[0]?.id ?? 'instagram',
    publishOn: localIsoDate(new Date()),
    status: 'idea',
    format: meta.formats[0]?.id ?? 'reel',
    pillar: null,
    title: '',
    caption: null,
    url: null,
    ideaId: null,
    ...draft,
  };
}

const NEXT_STATUS: Record<string, { status: string; label: string }> = {
  idea: { status: 'listo', label: 'Marcar listo' },
  listo: { status: 'publicado', label: 'Marcar publicado' },
};

export function CalendarPanel({ meta, draft, onDraftUsed }: { meta: MarketingMeta; draft: PostDraft | null; onDraftUsed: () => void }) {
  const today = new Date();
  const [month, setMonth] = useState({ year: today.getFullYear(), month: today.getMonth() });
  const [posts, setPosts] = useState<MarketingPost[] | null>(null);
  const [channel, setChannel] = useState('');
  const [form, setForm] = useState<MarketingPostInput>(() => blank(meta));
  const [editing, setEditing] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const range = monthRange(month.year, month.month);
  const load = useCallback(() => {
    getMarketingPosts(range.from, range.to).then(setPosts).catch((e: Error) => setError(e.message));
  }, [range.from, range.to]);

  useEffect(load, [load]);

  // Una idea de la biblioteca llega como borrador para programarla.
  useEffect(() => {
    if (!draft) return;
    setEditing(null);
    setForm(blank(meta, draft));
    onDraftUsed();
    document.getElementById('post-form')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, [draft, meta, onDraftUsed]);

  const visible = useMemo(() => (posts ?? []).filter((post) => !channel || post.channel === channel), [posts, channel]);
  const perChannel = useMemo(() => {
    const totals: Record<string, { planned: number; published: number }> = {};
    for (const post of posts ?? []) {
      const entry = totals[post.channel] ?? { planned: 0, published: 0 };
      entry.planned += 1;
      entry.published += post.status === 'publicado' ? 1 : 0;
      totals[post.channel] = entry;
    }
    return totals;
  }, [posts]);

  function set<K extends keyof MarketingPostInput>(key: K, value: MarketingPostInput[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function edit(post: MarketingPost) {
    setEditing(post.id);
    setForm({ channel: post.channel, publishOn: post.publishOn, status: post.status, format: post.format, pillar: post.pillar, title: post.title, caption: post.caption, url: post.url, ideaId: post.ideaId });
    document.getElementById('post-form')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function cancel() {
    setEditing(null);
    setForm(blank(meta));
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError('');
    try {
      await saveMarketingPost({ ...form, caption: form.caption?.trim() || null, url: form.url?.trim() || null }, editing ?? undefined);
      cancel();
      load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  }

  async function advance(post: MarketingPost) {
    const next = NEXT_STATUS[post.status];
    if (!next) return;
    setError('');
    try {
      await saveMarketingPost({ ...post, status: next.status }, post.id);
      load();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function remove(post: MarketingPost) {
    if (!window.confirm(`¿Borrar "${post.title}" del calendario?`)) return;
    try {
      await deleteMarketingPost(post.id);
      if (editing === post.id) cancel();
      load();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  const monthLabel = new Date(month.year, month.month, 1).toLocaleDateString('es-MX', { month: 'long', year: 'numeric' });
  const shift = (delta: number) => setMonth(({ year, month: m }) => {
    const next = new Date(year, m + delta, 1);
    return { year: next.getFullYear(), month: next.getMonth() };
  });

  return (
    <>
      <section className="adminCard" data-testid="marketing-calendar">
        <div className="adminRow adminRowSpread">
          <h2>Calendario</h2>
          <div className="adminRow marketingPeriods">
            <button type="button" className="secondaryButton" onClick={() => shift(-1)} aria-label="Mes anterior">←</button>
            <strong className="marketingMonth">{monthLabel}</strong>
            <button type="button" className="secondaryButton" onClick={() => shift(1)} aria-label="Mes siguiente">→</button>
          </div>
        </div>

        <div className="adminStats marketingCounts">
          {meta.channels.map((option) => (
            <button
              key={option.id}
              type="button"
              className="funnelStage"
              aria-pressed={channel === option.id}
              onClick={() => setChannel(channel === option.id ? '' : option.id)}
            >
              <strong>{perChannel[option.id]?.planned ?? 0}</strong>
              <span>{option.label}</span>
              <small>{perChannel[option.id]?.published ?? 0} publicadas</small>
            </button>
          ))}
        </div>

        {error ? <div className="errorBox" role="alert">{error}</div> : null}
        {posts === null && !error ? <p className="muted">Cargando…</p> : null}
        {posts && visible.length === 0 ? <p className="muted">No hay publicaciones {channel ? 'en esta red ' : ''}este mes. Agrega una abajo o prográmala desde Ideas.</p> : null}
        {visible.length ? (
          <div className="adminTableWrap">
            <table className="adminTable">
              <thead><tr><th>Fecha</th><th>Red</th><th>Tema</th><th>Formato</th><th>Estado</th><th></th></tr></thead>
              <tbody>
                {visible.map((post) => (
                  <tr key={post.id} data-testid="post-row">
                    <td className="customerVisits">{shortDay(post.publishOn)}</td>
                    <td>{post.channelLabel}</td>
                    <td>
                      {post.url ? <a href={post.url} target="_blank" rel="noreferrer">{post.title}</a> : post.title}
                      {post.pillarLabel ? <span className="adminSub">{post.pillarLabel}</span> : null}
                    </td>
                    <td>{post.formatLabel}</td>
                    <td><span className={`statusBadge stage-${post.status === 'publicado' ? 'ok' : post.status === 'listo' ? 'wait' : 'plain'}`}>{post.statusLabel}</span></td>
                    <td className="recordActions">
                      {NEXT_STATUS[post.status] ? <button type="button" className="hrLink" onClick={() => advance(post)}>{NEXT_STATUS[post.status].label}</button> : null}
                      <button type="button" className="hrLink marketingGap" onClick={() => edit(post)}>Editar</button>
                      <button type="button" className="linkButton" onClick={() => remove(post)}>Borrar</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>

      <form id="post-form" className="adminCard recordForm" onSubmit={submit} data-testid="post-form">
        <h2>{editing ? 'Editar publicación' : 'Nueva publicación'}</h2>
        <div className="recordGrid">
          <label>Red
            <select value={form.channel} onChange={(event) => set('channel', event.target.value)}>
              {meta.channels.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}
            </select>
          </label>
          <label>Fecha
            <input type="date" value={form.publishOn} onChange={(event) => set('publishOn', event.target.value)} required />
          </label>
          <label>Formato
            <select value={form.format} onChange={(event) => set('format', event.target.value)}>
              {meta.formats.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}
            </select>
          </label>
          <label>Pilar
            <select value={form.pillar ?? ''} onChange={(event) => set('pillar', event.target.value || null)}>
              <option value="">Sin pilar</option>
              {meta.pillars.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}
            </select>
          </label>
          <label>Estado
            <select value={form.status} onChange={(event) => set('status', event.target.value)}>
              {meta.statuses.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}
            </select>
          </label>
          <label>Enlace al post (al publicarlo)
            <input type="url" value={form.url ?? ''} onChange={(event) => set('url', event.target.value)} placeholder="https://" />
          </label>
        </div>
        <label className="recordNotes">Tema o gancho
          <input value={form.title} onChange={(event) => set('title', event.target.value)} maxLength={200} required data-testid="post-title" />
        </label>
        <label className="recordNotes">Texto de la publicación
          <textarea value={form.caption ?? ''} onChange={(event) => set('caption', event.target.value)} rows={4} placeholder="Opcional" />
        </label>
        <div className="adminRow">
          <button type="submit" className="primaryButton" disabled={saving || !form.title.trim()} data-testid="post-save">{editing ? 'Guardar cambios' : 'Agregar al calendario'}</button>
          {editing || form.ideaId ? <button type="button" className="secondaryButton" onClick={cancel}>Cancelar</button> : null}
        </div>
      </form>
    </>
  );
}
