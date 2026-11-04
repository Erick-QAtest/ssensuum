'use client';

import { useEffect, useMemo, useState } from 'react';
import { getMarketingPosts } from '../../lib/api';
import type { MarketingPost } from '../../lib/types';
import { localIsoDate } from '../booking/dates';
import { shortDay } from './marketing';

const MONTHS_AHEAD = 3;

// Algunos navegadores bloquean el portapapeles moderno: se intenta también con una selección temporal.
function copyWithSelection(text: string) {
  const area = document.createElement('textarea');
  area.value = text;
  area.setAttribute('readonly', '');
  area.style.position = 'absolute';
  area.style.left = '-9999px';
  document.body.appendChild(area);
  area.select();
  const copied = document.execCommand('copy');
  area.remove();
  return copied;
}

// Qué se publica, para qué y cómo pedírselo a la IA. Se edita desde el Calendario.
export function PlanPanel() {
  const [posts, setPosts] = useState<MarketingPost[] | null>(null);
  const [copied, setCopied] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    const today = new Date();
    const from = localIsoDate(new Date(today.getFullYear(), today.getMonth(), 1));
    const to = localIsoDate(new Date(today.getFullYear(), today.getMonth() + MONTHS_AHEAD + 1, 0));
    getMarketingPosts(from, to).then(setPosts).catch((e: Error) => setError(e.message));
  }, []);

  const sorted = useMemo(() => [...(posts ?? [])].sort((a, b) => a.publishOn.localeCompare(b.publishOn)), [posts]);

  function copy(post: MarketingPost) {
    setError('');
    const text = post.aiPrompt ?? '';
    (navigator.clipboard?.writeText(text) ?? Promise.reject())
      .catch(() => {
        if (!copyWithSelection(text)) throw new Error('copy');
      })
      .then(() => setCopied(post.id))
      .catch(() => setError('No se pudo copiar: abre el prompt y selecciónalo a mano.'));
  }

  return (
    <section className="adminCard" data-testid="marketing-plan">
      <h2>Plan y prompts</h2>
      <p className="muted">Cada publicación con su objetivo y el prompt para pedírsela a la IA. Revisa siempre el resultado antes de publicar; para cambiar algo, edítala en Calendario.</p>

      {error ? <div className="errorBox" role="alert">{error}</div> : null}
      {posts === null && !error ? <p className="muted">Cargando…</p> : null}
      {posts?.length === 0 ? <p className="muted">No hay publicaciones planeadas en los próximos meses.</p> : null}

      <ul className="planPosts">
        {sorted.map((post) => (
          <li key={post.id} className="planPost" data-testid="plan-post">
            <span className="adminSub">
              {shortDay(post.publishOn)} · {post.channelLabel} · {post.formatLabel}{post.pillarLabel ? ` · ${post.pillarLabel}` : ''} · {post.statusLabel}
            </span>
            <h3>{post.title}</h3>
            <p className="planLabel">Objetivo</p>
            <p>{post.objective ?? 'Sin definir.'}</p>
            {post.aiPrompt ? (
              <>
                <div className="adminRow">
                  <button type="button" className="secondaryButton" onClick={() => copy(post)} data-testid="plan-copy">
                    {copied === post.id ? 'Prompt copiado' : 'Copiar prompt'}
                  </button>
                </div>
                <details className="planPrompt">
                  <summary>Ver el prompt</summary>
                  <pre>{post.aiPrompt}</pre>
                </details>
              </>
            ) : <p className="muted">Sin prompt todavía.</p>}
          </li>
        ))}
      </ul>
    </section>
  );
}
