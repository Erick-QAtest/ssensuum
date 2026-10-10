import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'SSENSUUM · Private Massage Club',
  description: 'Masajes, barbería y medicina estética en Col. Americana, Guadalajara. Reserva tu experiencia SSENSUUM.',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es-MX">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Josefin+Sans:wght@300;400;500;600&family=Karla:wght@400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body>{children}</body>
    </html>
  );
}
