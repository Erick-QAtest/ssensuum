'use client';

import { FormEvent, useEffect, useMemo, useState } from 'react';
import { createMarketingIdea, deleteMarketingIdea, getMarketingIdeas } from '../../lib/api';
import type { MarketingIdea, MarketingMeta } from '../../lib/types';
import type { PostDraft } from './CalendarPanel';

export function IdeasPanel({ meta, onSchedule }: { meta: MarketingMeta; onSchedule: (draft: PostDraft) => void }) {
  const [ideas, setIdeas] = useState<MarketingIdea[] | null>(null);
  const [pillar, setPillar] = useState(meta.pillars[0]?.id ?? 'equipo');
  const [hook, setHook] = useState('');
  const [notes, setNotes] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getMarketingIdeas().then(setIdeas).catch((e: Error) => setError(e.message));
  }, []);

  const byPillar = useMemo(
    () => meta.pillars.map((option) => ({ ...option, ideas: (ideas ?? []).filter((idea) => idea.pillar === option.id) })),
    [ideas, meta.pillars],
  );

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError('');
    try {
      const idea = await createMarketingIdea({ pillar, hook, notes: notes.trim() || null });
      setIdeas((current) => [idea, ...(current ?? [])]);
      setHook('');
      setNotes('');
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  }

  async function remove(idea: MarketingIdea) {
    if (!window.confirm(`¿Borrar la idea "${idea.hook}"?`)) return;
    try {
      await deleteMarketingIdea(idea.id);
      setIdeas((current) => (current ?? []).filter((row) => row.id !== idea.id));
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <>
      <form className="adminCard recordForm" onSubmit={submit} data-testid="idea-form">
        <h2>Nueva idea</h2>
        <p className="muted">Guarda ganchos y temas por pilar para no empezar de cero cada semana. Desde aquí se programan en el calendario.</p>
        <div className="recordGrid">
          <label>Pilar
            <select value={pillar} onChange={(event) => setPillar(event.target.value)}>
              {meta.pillars.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}
            </select>
          </label>
          <label>Idea o gancho
            <input value={hook} onChange={(event) => setHook(event.target.value)} maxLength={200} required placeholder="Ej. ¿Presión firme o suave? Así lo decides" data-testid="idea-hook" />
          </label>
        </div>
        <label className="recordNotes">Notas
          <input value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="Opcional: tomas, audio, a quién grabar" />
        </label>
        {error ? <div className="errorBox" role="alert">{error}</div> : null}
        <div className="adminRow">
          <button type="submit" className="primaryButton" disabled={saving || !hook.trim()} data-testid="idea-save">Guardar idea</button>
        </div>
      </form>

      {ideas === null && !error ? <p className="muted">Cargando…</p> : null}
      {ideas ? (
        <section className="adminCard">
          <h2>Biblioteca</h2>
          {byPillar.map((group) => (
            <div key={group.id} className="marketingPillar">
              <h3 className="hrSubhead">{group.label} <span className="adminSub marketingInline">{group.ideas.length}</span></h3>
              {group.ideas.length === 0 ? <p className="adminSub">Sin ideas todavía.</p> : (
                <ul className="hrTemplates">
                  {group.ideas.map((idea) => (
                    <li key={idea.id} data-testid="idea-row">
                      <div>
                        <strong>{idea.hook}</strong>
                        {idea.notes ? <span className="adminSub">{idea.notes}</span> : null}
                        <span className="adminSub">{idea.used ? `Usada ${idea.used === 1 ? '1 vez' : `${idea.used} veces`}` : 'Sin usar'}</span>
                      </div>
                      <div className="recordActions">
                        <button type="button" className="hrLink" onClick={() => onSchedule({ title: idea.hook, pillar: idea.pillar, ideaId: idea.id })}>Programar</button>
                        <button type="button" className="linkButton" onClick={() => remove(idea)}>Borrar</button>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </section>
      ) : null}
    </>
  );
}
