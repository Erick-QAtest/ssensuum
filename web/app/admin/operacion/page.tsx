import type { Metadata } from 'next';
import { OperationsPage } from '../../../features/operations/OperationsPage';

export const metadata: Metadata = { title: 'Operación · SSENSUUM' };

export default function AdminOperationsPage() {
  return <OperationsPage />;
}
