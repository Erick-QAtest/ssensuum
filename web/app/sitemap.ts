import type { MetadataRoute } from 'next';

const BASE = 'https://ssensuum.mx';

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    { url: BASE, changeFrequency: 'weekly', priority: 1 },
    { url: `${BASE}/quiz`, changeFrequency: 'monthly', priority: 0.6 },
    { url: `${BASE}/terminos`, changeFrequency: 'yearly', priority: 0.3 },
    { url: `${BASE}/aviso-de-privacidad`, changeFrequency: 'yearly', priority: 0.3 },
  ];
}
