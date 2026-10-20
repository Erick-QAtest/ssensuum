import type { Metadata } from 'next';
import { HrPage } from '../../../features/hr/HrPage';

export const metadata: Metadata = { title: 'Recursos humanos · SSENSUUM' };

export default function AdminHrPage() {
  return <HrPage />;
}
