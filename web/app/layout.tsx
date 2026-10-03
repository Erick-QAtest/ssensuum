import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'SSENSUUM · Private Massage Club en Guadalajara',
  description: 'Diseña tu masaje: elige técnicas, presión, zonas, terapeuta, día y hora en SSENSUUM Private Massage Club, Guadalajara.'
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es-MX">
      <body>{children}</body>
    </html>
  );
}
