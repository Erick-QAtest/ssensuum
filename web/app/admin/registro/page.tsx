import type { Metadata } from 'next';
import { RecordsPage } from '../../../features/records/RecordsPage';

export const metadata: Metadata = { title: 'Registro · SSENSUUM' };

export default function AdminRecordsPage() {
  return <RecordsPage />;
}
