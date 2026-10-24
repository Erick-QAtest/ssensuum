import type { Metadata } from 'next';
import './globals.css';

const DESCRIPTION = 'Masaje privado para hombres en la Col. Americana, Guadalajara. Eliges terapeuta, técnica, presión y zonas, a tu ritmo.';

export const metadata: Metadata = {
  metadataBase: new URL('https://ssensuum.mx'),
  title: 'SSENSUUM · Club privado de masaje en Guadalajara',
  description: DESCRIPTION,
  openGraph: {
    type: 'website',
    locale: 'es_MX',
    siteName: 'SSENSUUM',
    title: 'SSENSUUM · Tú eliges quién te atiende',
    description: DESCRIPTION,
    images: [{ url: '/ssensuum/og-cabina.jpg', width: 1200, height: 630, alt: 'Cabina privada de SSENSUUM a media luz' }],
  },
  twitter: { card: 'summary_large_image' },
};

// Datos estructurados para Google (búsqueda local y Maps).
const LOCAL_BUSINESS = {
  '@context': 'https://schema.org',
  '@type': 'DaySpa',
  name: 'SSENSUUM',
  description: DESCRIPTION,
  url: 'https://ssensuum.mx',
  image: 'https://ssensuum.mx/ssensuum/location.jpg',
  logo: 'https://ssensuum.mx/ssensuum/brand-logo.jpg',
  telephone: '+52 33 1068 1307',
  priceRange: '$$',
  address: {
    '@type': 'PostalAddress',
    streetAddress: 'Mexicaltzingo 2122-B, Col. Americana',
    addressLocality: 'Guadalajara',
    addressRegion: 'Jalisco',
    addressCountry: 'MX',
  },
  geo: { '@type': 'GeoCoordinates', latitude: 20.6684, longitude: -103.3757 },
  hasMap: 'https://maps.app.goo.gl/2CLVeFkfyoiGDQqv6',
  openingHoursSpecification: [{
    '@type': 'OpeningHoursSpecification',
    dayOfWeek: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
    opens: '09:00',
    closes: '20:30',
  }],
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es-MX">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Karla:wght@400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body>
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(LOCAL_BUSINESS) }} />
        {children}
      </body>
    </html>
  );
}
