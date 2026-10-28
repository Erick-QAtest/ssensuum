// Red de la que llegó la visita: el enlace de cada red trae ?utm_source=ig (o tt, x, fb);
// sin enlace marcado se usa el sitio de referencia. Se recuerda la primera para atribuir la reserva.
const STORAGE_KEY = 'ssensuum.channel';
const REMEMBER_DAYS = 90;

function fromUrl(): string | null {
  const params = new URLSearchParams(window.location.search);
  const value = params.get('utm_source') ?? params.get('ref');
  if (value) return value.slice(0, 200);
  const referrer = document.referrer;
  if (!referrer) return null;
  try {
    return new URL(referrer).host === window.location.host ? null : referrer.slice(0, 200);
  } catch {
    return null;
  }
}

export function currentChannel(): string | undefined {
  try {
    const stored = JSON.parse(window.localStorage.getItem(STORAGE_KEY) ?? 'null') as { channel: string; at: number } | null;
    if (stored && Date.now() - stored.at < REMEMBER_DAYS * 86_400_000) return stored.channel;
    const channel = fromUrl();
    if (!channel) return undefined;
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify({ channel, at: Date.now() }));
    return channel;
  } catch {
    // Sin almacenamiento se usa solo lo que traiga esta página.
    try {
      return fromUrl() ?? undefined;
    } catch {
      return undefined;
    }
  }
}
