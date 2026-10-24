import type { Metadata } from 'next';
import { Catalog } from '../features/catalog/Catalog';

export const metadata: Metadata = {
  alternates: { canonical: '/' },
};

export default function HomePage() {
  return <Catalog />;
}
