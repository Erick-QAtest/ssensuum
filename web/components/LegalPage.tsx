import Link from 'next/link';
import { BUSINESS } from '../lib/business';

export function LegalPage({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <main className="bookingShell">
      <Link href="/" className="backLink">← Volver a SSENSUUM</Link>
      <article className="bookingPanel legalPage">
        <span className="kicker">{BUSINESS.commercialName}</span>
        <h1>{title}</h1>
        <p className="legalUpdated">Última actualización: {BUSINESS.lastUpdated}</p>
        {children}
      </article>
    </main>
  );
}
